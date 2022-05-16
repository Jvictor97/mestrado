import sys
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
  QApplication, 
  QWidget, 
  QFormLayout, 
  QVBoxLayout, 
  QHBoxLayout,
  QPushButton,
  QDialogButtonBox,
  QLineEdit, 
  QLabel,
  QRadioButton,
  QMessageBox
)

def clicked():
  print('clicou!')


class MainWindow(QWidget):
  def __init__(self):
    super().__init__()

    # QWidget { background-color: #262626; color: white }
    # QLineEdit { border: 1px solid white }
    self.setStyleSheet("""
      QLineEdit { height: 30px; border-radius: 5px; padding: 1px 3px }
      QLabel { font-size: 16px }
    """)
    self.setMinimumWidth(500)
    self.setup()

  def setup(self):
    self.setWindowTitle('Neuropróteses - Sistema de Monitoramento de Progresso')

    self.setupInnerLayout()

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

    patient_email_label = QLabel('Email')
    patient_email_edit = QLineEdit()
    patient_email_edit.setPlaceholderText('jose@gmail.com')

    patient_password_label = QLabel('Senha')
    patient_password_edit = QLineEdit()
    patient_password_edit.setPlaceholderText('********')
    patient_password_edit.setEchoMode(QLineEdit.Password)

    patient_form_layout.addRow(patient_email_label, patient_email_edit)
    patient_form_layout.addRow(patient_password_label, patient_password_edit)

    # Setup layout for exercise data
    options_label = QLabel('Dados do Monitoramento')
    options_label.setStyleSheet('margin-top: 20px; font-weight: bold')
    main_layout.addWidget(options_label)

    app_form_layout = QFormLayout()
    main_layout.addLayout(app_form_layout)

    exercise_label = QLabel('Exercício')
    exercise_edit = QLineEdit()
    exercise_edit.setPlaceholderText('ex: open-hand, finger-extension, ...')

    app_form_layout.addRow(exercise_label, exercise_edit)

    # Setup config layout
    options_label = QLabel('Configurações')
    options_label.setStyleSheet('margin-top: 20px; font-weight: bold')
    main_layout.addWidget(options_label)

    options_layout = QHBoxLayout()
    main_layout.addLayout(options_layout)

    ## Lado da mão
    hand_radio_layout = QVBoxLayout()
    options_layout.addLayout(hand_radio_layout)

    hand_radio_title = QLabel('Mão capturada')
    hand_radio_layout.addWidget(hand_radio_title)

    left_hand_side = QRadioButton('Esquerda')
    right_hand_side = QRadioButton('Direita')

    hand_radio_layout.addWidget(left_hand_side)
    hand_radio_layout.addWidget(right_hand_side)

    ## Gold Standard ou Follow Up?
    monitoring_type_layout = QVBoxLayout()
    options_layout.addLayout(monitoring_type_layout)

    monitoring_type_label = QLabel('Tipo de captura')
    monitoring_type_layout.addWidget(monitoring_type_label)

    gold_standard_radio = QRadioButton('Padrão-ouro')
    follow_up_radio = QRadioButton('Acompanhamento')

    monitoring_type_layout.addWidget(gold_standard_radio)
    monitoring_type_layout.addWidget(follow_up_radio)

    # Botões
    button_box = QDialogButtonBox()

    button_box.addButton('Iniciar', QDialogButtonBox.ButtonRole.AcceptRole)
    button_box.addButton('Cancelar', QDialogButtonBox.ButtonRole.RejectRole)

    start_button, cancel_button = button_box.buttons()

    start_button.clicked.connect(clicked)
    cancel_button.clicked.connect(self.close_app)

    main_layout.addWidget(button_box)

  def close_app(self):
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
  window = MainWindow()
  window.show()

  sys.exit(app.exec())

if __name__ == '__main__':
  run()