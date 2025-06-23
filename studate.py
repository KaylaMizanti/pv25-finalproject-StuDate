import sys, sqlite3, csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QCheckBox, QDateEdit, QFileDialog, QScrollArea,
    QStatusBar, QHeaderView, QWidget, QAction, QMenuBar
)
from PyQt5.QtCore import Qt, QDate


class StuDate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StuDate")
        self.setGeometry(100, 100, 1000, 600)
        self.conn = sqlite3.connect("studate.db")
        self.cursor = self.conn.cursor()
        self.create_table()
        self.last_focused_input = None

        # UI setup
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.setup_menu()
        self.init_ui()
        self.load_data()

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        export_action = QAction("Export ke CSV", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: QMessageBox.information(self, "Tentang", "Aplikasi StuDate dibuat oleh Kayla Mizanti\nNIM: F1D022127"))
        menubar.addAction(about_action)

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matkul TEXT,
            judul TEXT,
            deadline TEXT,
            status TEXT,
            catatan TEXT,
            prioritas INTEGER
        )""")
        self.conn.commit()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Welcome to StuDate! 📚")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Form
        form_layout = QHBoxLayout()
        self.matkul_input = QLineEdit(placeholderText="Nama Mata Kuliah")
        self.judul_input = QLineEdit(placeholderText="Judul Tugas")
        self.catatan_input = QTextEdit()
        self.catatan_input.setPlaceholderText("Catatan")
        self.catatan_input.setFixedHeight(30)
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        self.prioritas_input = QCheckBox("Prioritas")

        for w in [self.matkul_input, self.judul_input, self.catatan_input, self.date_input]:
            w.installEventFilter(self)

        form_layout.addWidget(self.matkul_input)
        form_layout.addWidget(self.judul_input)
        form_layout.addWidget(self.catatan_input)
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(self.prioritas_input)
        layout.addLayout(form_layout)

        # Search & Paste
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="Cari matkul atau tugas...")
        self.search_input.textChanged.connect(self.search_task)
        self.search_input.installEventFilter(self)
        self.paste_button = QPushButton("📋")
        self.paste_button.setFixedWidth(40)
        self.paste_button.clicked.connect(self.paste_clipboard)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.paste_button)
        layout.addLayout(search_layout)

        # Tombol
        pink = """
        QPushButton {
            background-color: #d63384;
            color: white;
            border-radius: 5px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #e83e8c;
        }
        """
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Tambah Tugas")
        self.add_button.setStyleSheet(pink)
        self.add_button.clicked.connect(self.add_task)

        self.delete_button = QPushButton("Hapus Tugas")
        self.delete_button.setStyleSheet(pink)
        self.delete_button.clicked.connect(self.delete_task)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tampilkan Semua", "Belum Dikerjakan", "Selesai"])
        self.filter_combo.currentTextChanged.connect(self.filter_status)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.filter_combo)
        layout.addLayout(button_layout)

        # Tabel
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Mata Kuliah", "Judul Tugas", "Deadline", "Status", "Catatan"])
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.cellClicked.connect(self.handle_cell_click)
        self.table.itemChanged.connect(self.update_cell)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.table)
        layout.addWidget(scroll)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("👩 Nama: Kayla Mizanti | NIM: F1D022127")

        # Set layout
        self.main_widget.setLayout(layout)

    def eventFilter(self, source, event):
        if event.type() == event.FocusIn:
            self.last_focused_input = source
        return super().eventFilter(source, event)

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        if isinstance(self.last_focused_input, QLineEdit):
            self.last_focused_input.setText(clipboard.text())
        elif isinstance(self.last_focused_input, QTextEdit):
            self.last_focused_input.setPlainText(clipboard.text())

    def add_task(self):
        matkul = self.matkul_input.text().strip()
        judul = self.judul_input.text().strip()
        catatan = self.catatan_input.toPlainText().strip()
        deadline = self.date_input.date().toString("yyyy-MM-dd")
        prioritas = 1 if self.prioritas_input.isChecked() else 0

        if not matkul or not judul:
            QMessageBox.warning(self, "Input Salah", "Matkul dan Judul wajib diisi!")
            return

        self.cursor.execute("""
        INSERT INTO tugas (matkul, judul, deadline, status, catatan, prioritas)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (matkul, judul, deadline, "Belum Dikerjakan", catatan, prioritas))
        self.conn.commit()
        self.clear_inputs()
        self.load_data()
        QMessageBox.information(self, "Berhasil", f"Tugas '{judul}' berhasil ditambahkan!")

    def clear_inputs(self):
        self.matkul_input.clear()
        self.judul_input.clear()
        self.catatan_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.prioritas_input.setChecked(False)

    def load_data(self, filter_status=None, search_term=None):
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        query = "SELECT id, matkul, judul, deadline, status, catatan, prioritas FROM tugas"
        params = []

        if filter_status in ("Belum Dikerjakan", "Selesai"):
            query += " WHERE status = ?"
            params.append(filter_status)

        if search_term:
            clause = "(matkul LIKE ? OR judul LIKE ?)"
            if "WHERE" in query:
                query += " AND " + clause
            else:
                query += " WHERE " + clause
            params.extend([f"%{search_term}%"] * 2)

        self.cursor.execute(query, params)
        for row_idx, (id_, matkul, judul, deadline, status, catatan, prioritas) in enumerate(self.cursor.fetchall()):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(id_)))
            matkul_display = "🔥 " + matkul if prioritas else matkul
            self.table.setItem(row_idx, 1, QTableWidgetItem(matkul_display))
            self.table.setItem(row_idx, 2, QTableWidgetItem(judul))
            self.table.setItem(row_idx, 3, QTableWidgetItem(deadline))

            status_item = QTableWidgetItem(status)
            if status.lower() == "belum dikerjakan":
                status_item.setForeground(Qt.red)
            else:
                status_item.setForeground(Qt.black)
            self.table.setItem(row_idx, 4, status_item)

            self.table.setItem(row_idx, 5, QTableWidgetItem(catatan))

        self.table.blockSignals(False)

    def handle_cell_click(self, row, col):
        if col == 4:
            current_status = self.table.item(row, col).text()
            if current_status.lower() == "belum dikerjakan":
                confirm = QMessageBox.question(
                    self, "Ubah Status", "Ubah status menjadi 'Selesai'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    id_ = self.table.item(row, 0).text()
                    self.cursor.execute("UPDATE tugas SET status = ? WHERE id = ?", ("Selesai", id_))
                    self.conn.commit()
                    self.load_data(
                        self.filter_combo.currentText() if self.filter_combo.currentText() != "Tampilkan Semua" else None,
                        self.search_input.text()
                    )

    def update_cell(self, item):
        row = item.row()
        col = item.column()
        if col == 5:  # Catatan bisa diedit
            id_ = self.table.item(row, 0).text()
            new_value = item.text()
            self.cursor.execute("UPDATE tugas SET catatan = ? WHERE id = ?", (new_value, id_))
            self.conn.commit()

    def delete_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Hapus", "Pilih tugas yang ingin dihapus.")
            return
        id_item = self.table.item(selected, 0)
        judul_item = self.table.item(selected, 2)
        if id_item and judul_item:
            judul_text = judul_item.text()
            confirm = QMessageBox.question(self, "Konfirmasi", f"Yakin ingin menghapus tugas '{judul_text}'?",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.cursor.execute("DELETE FROM tugas WHERE id = ?", (id_item.text(),))
                self.conn.commit()
                self.load_data()
                QMessageBox.information(self, "Dihapus", f"Tugas '{judul_text}' berhasil dihapus.")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "", "CSV Files (*.csv)")
        if path:
            self.cursor.execute("SELECT id, matkul, judul, deadline, status, catatan FROM tugas")
            rows = self.cursor.fetchall()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Mata Kuliah", "Judul Tugas", "Deadline", "Status", "Catatan"])
                writer.writerows(rows)
            QMessageBox.information(self, "Berhasil", "Data berhasil diekspor ke CSV.")

    def search_task(self, text):
        self.load_data(
            self.filter_combo.currentText() if self.filter_combo.currentText() != "Tampilkan Semua" else None,
            text
        )

    def filter_status(self, status):
        self.load_data(
            status if status != "Tampilkan Semua" else None,
            self.search_input.text()
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StuDate()
    window.show()
    sys.exit(app.exec_())
