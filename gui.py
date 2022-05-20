import sys
from PySide6.QtGui import QCloseEvent, QIcon, QPalette, QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
  QApplication, 
  QWidget, 
  QFormLayout, 
  QVBoxLayout, 
  QHBoxLayout,
  QDialogButtonBox,
  QLineEdit, 
  QLabel,
  QRadioButton,
  QMessageBox,
  QGroupBox,
)
from main import runExerciseRecorder

class MainWindow(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)

    # QWidget { background-color: #262626; color: white }
    # QLineEdit { border: 1px solid white }
    self.setStyleSheet("""
      QLineEdit { height: 30px; padding: 1px 10px; }
      QLabel { font-size: 16px }
    """)
    self.setMinimumWidth(500)
    self.move(2500, 400)
    self.setup()

  def setup(self):
    self.setWindowTitle('Neuropróteses - Sistema de Monitoramento de Progresso')
    self.setWindowIcon(QIcon('icon.png'))
    self.setupInnerLayout()

  def handleClick(self):
    parameters = {
      'gold_standard': self.gold_standard_radio.isChecked(),
      'patient_email': self.patient_email_edit.text(),
      'patient_password': self.patient_password_edit.text(),
      'exercise': self.exercise_edit.text(),
      'hand_side': 'left' if self.left_hand_side.isChecked() else 'right'
    }

    self.hide()
    runExerciseRecorder(
      fromCLI=False, 
      parameters=parameters, 
      handleClose=self.handleRecorderClose
    )

  def handleRecorderClose(self):
    self.show()

  def setupInnerLayout(self):
    # Setup main layout
    main_layout = QVBoxLayout()
    self.setLayout(main_layout)

    # Setup layout for patient data
    patient_label = QLabel('Dados do Paciente')
    patient_label.setStyleSheet('margin-top: 5px; font-weight: bold')
    main_layout.addWidget(patient_label)

    patient_form_layout = QFormLayout()
    main_layout.addLayout(patient_form_layout)

    patient_email_label = QLabel('Email:')
    self.patient_email_edit = QLineEdit()
    self.patient_email_edit.setPlaceholderText('jose@gmail.com')

    patient_password_label = QLabel('Senha:')
    self.patient_password_edit = QLineEdit()
    self.patient_password_edit.setPlaceholderText('********')
    self.patient_password_edit.setEchoMode(QLineEdit.Password)

    patient_form_layout.addRow(patient_email_label, self.patient_email_edit)
    patient_form_layout.addRow(patient_password_label, self.patient_password_edit)

    # Setup layout for exercise data
    options_label = QLabel('Dados do Monitoramento')
    options_label.setStyleSheet('margin-top: 20px; font-weight: bold')
    main_layout.addWidget(options_label)

    app_form_layout = QFormLayout()
    main_layout.addLayout(app_form_layout)

    exercise_label = QLabel('Exercício:')
    self.exercise_edit = QLineEdit()
    self.exercise_edit.setPlaceholderText('ex: open-hand, finger-extension, ...')

    app_form_layout.addRow(exercise_label, self.exercise_edit)

    # Setup config layout
    options_label = QLabel('Configurações')
    options_label.setStyleSheet('margin-top: 20px; font-weight: bold')
    main_layout.addWidget(options_label)

    options_layout = QHBoxLayout()
    main_layout.addLayout(options_layout)

    ## Lado da mão
    hand_radio_layout = QVBoxLayout()

    hand_radio_group = QGroupBox('Mão capturada')
    self.left_hand_side = QRadioButton('Esquerda')
    self.left_hand_side.setChecked(True)
    self.right_hand_side = QRadioButton('Direita')

    hand_radio_layout.addWidget(self.left_hand_side)
    hand_radio_layout.addWidget(self.right_hand_side)

    hand_radio_group.setLayout(hand_radio_layout)

    options_layout.addWidget(hand_radio_group)

    ## Gold Standard ou Follow Up?
    monitoring_type_layout = QVBoxLayout()
    # options_layout.addLayout(monitoring_type_layout)

    # monitoring_type_label = QLabel('Tipo de captura')
    # monitoring_type_layout.addWidget(monitoring_type_label)

    monitoring_type_group = QGroupBox('Tipo de captura')
    self.gold_standard_radio = QRadioButton('Padrão-ouro')
    self.gold_standard_radio.setChecked(True)
    self.follow_up_radio = QRadioButton('Acompanhamento')

    monitoring_type_layout.addWidget(self.gold_standard_radio)
    monitoring_type_layout.addWidget(self.follow_up_radio)

    monitoring_type_group.setLayout(monitoring_type_layout)

    options_layout.addWidget(monitoring_type_group)

    # Botões
    button_box = QDialogButtonBox()

    button_box.addButton('Iniciar', QDialogButtonBox.ButtonRole.AcceptRole)
    button_box.addButton('Cancelar', QDialogButtonBox.ButtonRole.RejectRole)

    start_button, cancel_button = button_box.buttons()

    start_button.clicked.connect(self.handleClick)
    cancel_button.clicked.connect(self.closeApp)

    main_layout.addWidget(button_box)

  def closeApp(self):
    QApplication.instance().quit()

  def closeEvent(self, event: QCloseEvent):
    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Question)
    message_box.setWindowTitle('Confirme')
    message_box.setText('Deseja mesmo fechar a aplicação?')
    message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    confirm_button = message_box.button(QMessageBox.Yes)
    confirm_button.setText('Sim')

    cancel_button = message_box.button(QMessageBox.No)
    cancel_button.setText('Não')

    message_box.exec()

    if message_box.clickedButton() == confirm_button:
      event.accept()
    else:
      event.ignore()


def run():
  app = QApplication(sys.argv)

  # Force the style to be the same on all OSs:
  app.setStyle("Fusion")

  # Now use a palette to switch to dark colors:
  palette = QPalette()

  palette.setColor(QPalette.Window, QColor(53, 53, 53))
  palette.setColor(QPalette.WindowText, Qt.white)
  palette.setColor(QPalette.Base, QColor(25, 25, 25))
  palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
  palette.setColor(QPalette.ToolTipBase, Qt.black)
  palette.setColor(QPalette.ToolTipText, Qt.white)
  palette.setColor(QPalette.Text, Qt.white)
  palette.setColor(QPalette.Button, QColor(53, 53, 53))
  palette.setColor(QPalette.ButtonText, Qt.white)
  palette.setColor(QPalette.BrightText, Qt.red)
  palette.setColor(QPalette.Link, QColor(42, 130, 218))
  palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
  palette.setColor(QPalette.HighlightedText, Qt.black)

  palette.setColor(QPalette.PlaceholderText, QColor('gray'))
  app.setPalette(palette)

  window = MainWindow()
  window.show()

  sys.exit(app.exec())

if __name__ == '__main__':
  run()