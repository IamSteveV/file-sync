"""File preview dialog for viewing file contents."""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional
from PIL import Image, ImageTk


class FilePreviewDialog(ctk.CTkToplevel):
    """Dialog for previewing file contents."""

    def __init__(self, parent, file_path: Path, file_name: str):
        """
        Initialize file preview dialog.

        Args:
            parent: Parent window
            file_path: Path to file to preview
            file_name: Display name of the file
        """
        super().__init__(parent)

        self.file_path = Path(file_path)
        self.file_name = file_name

        self.title(f"Preview: {file_name}")
        self.geometry("800x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_preview()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="gray20")
        header_frame.pack(fill="x")

        ctk.CTkLabel(
            header_frame,
            text=self.file_name,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        # File info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)

        if self.file_path.exists():
            size = self.file_path.stat().st_size
            size_str = self._format_size(size)

            info_text = f"Path: {self.file_path} • Size: {size_str}"
        else:
            info_text = "File not found locally (may need to download from provider)"

        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")

        # Preview container
        self.preview_frame = ctk.CTkScrollableFrame(self)
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=120,
            height=40
        ).pack(pady=20)

    def _load_preview(self):
        """Load and display file preview."""
        if not self.file_path.exists():
            self._show_error("File not found locally")
            return

        file_ext = self.file_path.suffix.lower()

        try:
            if file_ext in ['.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css', '.yaml', '.yml', '.log']:
                self._preview_text()
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                self._preview_image()
            elif file_ext == '.pdf':
                self._preview_pdf()
            else:
                self._show_unsupported()

        except Exception as e:
            self._show_error(f"Error loading preview: {str(e)}")

    def _preview_text(self):
        """Preview text file."""
        try:
            # Try to read as text
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100000)  # Limit to 100KB

            # Create text widget
            textbox = ctk.CTkTextbox(
                self.preview_frame,
                wrap="word",
                font=ctk.CTkFont(family="monospace", size=11)
            )
            textbox.pack(fill="both", expand=True)

            textbox.insert("1.0", content)
            textbox.configure(state="disabled")

        except Exception as e:
            self._show_error(f"Error reading text file: {str(e)}")

    def _preview_image(self):
        """Preview image file."""
        try:
            # Load image
            image = Image.open(self.file_path)

            # Get preview frame size
            max_width = 760
            max_height = 500

            # Calculate scaling
            width, height = image.size
            scale = min(max_width / width, max_height / height, 1.0)

            if scale < 1.0:
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Create label to display image
            image_label = ctk.CTkLabel(
                self.preview_frame,
                text="",
                image=photo
            )
            image_label.image = photo  # Keep a reference
            image_label.pack(pady=20)

            # Show image info
            info_label = ctk.CTkLabel(
                self.preview_frame,
                text=f"Original size: {width} x {height} pixels",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            info_label.pack()

        except Exception as e:
            self._show_error(f"Error loading image: {str(e)}")

    def _preview_pdf(self):
        """Preview PDF file (basic info only)."""
        try:
            # PDF preview requires additional libraries (PyPDF2, pdf2image)
            # For now, show basic info
            info_text = """PDF Preview

This file is a PDF document.

Full PDF preview requires additional dependencies:
• PyPDF2 (for text extraction)
• pdf2image (for rendering)

To view this file, please use your system's PDF viewer.
You can open it from the file browser."""

            label = ctk.CTkLabel(
                self.preview_frame,
                text=info_text,
                font=ctk.CTkFont(size=13),
                justify="left"
            )
            label.pack(pady=40)

            # Try to extract basic PDF info
            try:
                import PyPDF2
                with open(self.file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    num_pages = len(pdf.pages)

                    info_label = ctk.CTkLabel(
                        self.preview_frame,
                        text=f"Pages: {num_pages}",
                        font=ctk.CTkFont(size=12),
                        text_color="gray"
                    )
                    info_label.pack()

            except ImportError:
                pass  # PyPDF2 not installed
            except Exception as e:
                pass  # Error reading PDF

            # Add button to open in system viewer
            ctk.CTkButton(
                self.preview_frame,
                text="Open in System Viewer",
                command=self._open_in_system,
                width=180,
                height=40
            ).pack(pady=20)

        except Exception as e:
            self._show_error(f"Error previewing PDF: {str(e)}")

    def _show_error(self, message: str):
        """Show error message."""
        label = ctk.CTkLabel(
            self.preview_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14),
            text_color="red"
        )
        label.pack(pady=40)

    def _show_unsupported(self):
        """Show unsupported file type message."""
        file_ext = self.file_path.suffix.lower()

        message = f"""File type '{file_ext}' preview not supported.

Supported formats:
• Text files: .txt, .md, .py, .js, .json, .xml, .html, etc.
• Images: .jpg, .png, .gif, .bmp
• PDF: .pdf (limited support)

To view this file, please use an appropriate application."""

        label = ctk.CTkLabel(
            self.preview_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            justify="left"
        )
        label.pack(pady=40)

        # Add button to open in system viewer
        ctk.CTkButton(
            self.preview_frame,
            text="Open in System Viewer",
            command=self._open_in_system,
            width=180,
            height=40
        ).pack(pady=20)

    def _open_in_system(self):
        """Open file in system default application."""
        import platform
        import subprocess

        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(self.file_path)])
            elif platform.system() == 'Windows':
                subprocess.run(['start', str(self.file_path)], shell=True)
            else:  # Linux
                subprocess.run(['xdg-open', str(self.file_path)])

            messagebox.showinfo(
                "Opened",
                f"File opened in system default application",
                parent=self
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to open file:\n{str(e)}",
                parent=self
            )

    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class QuickPreviewPanel(ctk.CTkFrame):
    """Side panel for quick file preview without opening new window."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="gray20")

        self.current_file = None

        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Header
        ctk.CTkLabel(
            self,
            text="Quick Preview",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # Preview area
        self.preview_area = ctk.CTkFrame(self, fg_color="gray25")
        self.preview_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no file selected."""
        for widget in self.preview_area.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.preview_area,
            text="Select a file to preview",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=40)

    def preview_file(self, file_path: Path, file_name: str):
        """Show quick preview of a file."""
        self.current_file = file_path

        # Clear previous preview
        for widget in self.preview_area.winfo_children():
            widget.destroy()

        # Show file name
        name_label = ctk.CTkLabel(
            self.preview_area,
            text=file_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=250
        )
        name_label.pack(pady=(15, 5))

        if not file_path.exists():
            ctk.CTkLabel(
                self.preview_area,
                text="File not available locally",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=20)
            return

        file_ext = file_path.suffix.lower()

        try:
            # Show thumbnail for images
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                self._show_image_thumbnail(file_path)

            # Show first few lines for text
            elif file_ext in ['.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css']:
                self._show_text_preview(file_path)

            # Show file info
            else:
                size = file_path.stat().st_size
                size_str = self._format_size(size)

                ctk.CTkLabel(
                    self.preview_area,
                    text=f"Type: {file_ext}\nSize: {size_str}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                ).pack(pady=20)

        except Exception as e:
            ctk.CTkLabel(
                self.preview_area,
                text=f"Preview error:\n{str(e)}",
                font=ctk.CTkFont(size=10),
                text_color="red",
                wraplength=250
            ).pack(pady=20)

    def _show_image_thumbnail(self, file_path: Path):
        """Show image thumbnail."""
        try:
            image = Image.open(file_path)
            image.thumbnail((250, 250), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)

            image_label = ctk.CTkLabel(
                self.preview_area,
                text="",
                image=photo
            )
            image_label.image = photo
            image_label.pack(pady=10)

        except Exception as e:
            ctk.CTkLabel(
                self.preview_area,
                text=f"Error loading image",
                font=ctk.CTkFont(size=10),
                text_color="red"
            ).pack(pady=20)

    def _show_text_preview(self, file_path: Path):
        """Show text file preview."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:10]  # First 10 lines
                preview_text = ''.join(lines)

                if len(lines) == 10:
                    preview_text += "\n..."

            textbox = ctk.CTkTextbox(
                self.preview_area,
                height=200,
                font=ctk.CTkFont(family="monospace", size=9),
                wrap="word"
            )
            textbox.pack(fill="both", expand=True, padx=10, pady=10)

            textbox.insert("1.0", preview_text)
            textbox.configure(state="disabled")

        except Exception as e:
            ctk.CTkLabel(
                self.preview_area,
                text="Error reading file",
                font=ctk.CTkFont(size=10),
                text_color="red"
            ).pack(pady=20)

    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
