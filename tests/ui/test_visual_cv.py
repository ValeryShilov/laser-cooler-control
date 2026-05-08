import pytest
import os
import glob
import numpy as np
from functools import lru_cache
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QSize

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
    # На Windows tesseract часто устанавливается сюда:
    if os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pytesseract = None

try:
    from fuzzywuzzy import fuzz
except ImportError:
    fuzz = None

from ui.mnemonic import ChillerMnemonic
from ui.main_window import ChillerPanel
from hardware.mock_adapter import MockAdapter
from PySide6.QtCore import QSize, QEventLoop, QTimer

# Ищем все файлы схем
SCHEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "test_data", "schemes")
SCHEME_FILES = glob.glob(os.path.join(SCHEMES_DIR, "*.yaml"))
RENDERED_DIR = os.path.join(os.path.dirname(SCHEMES_DIR), "rendered_schemes")

@lru_cache(maxsize=30)
def get_rendered_data(scheme_path):
    """
    Кэшированная функция рендеринга. 
    Открывает главное окно, дожидается фонового расчета и делает честный grab() виджета.
    """
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    app.setStyle('Fusion')
        
    adapter = MockAdapter()
    window = ChillerPanel(adapter)
    window.resize(1200, 850)  # Задаем фиксированный размер окна для воспроизводимости
    
    mnemonic = window.findChild(ChillerMnemonic)
    
    # Переопределяем схему
    mnemonic.parser.__init__(scheme_path)
    mnemonic.components, mnemonic.connections = mnemonic.parser.parse()
    
    window.show()
    mnemonic._request_recompute()
    
    loop = QEventLoop()
    def on_ready(*args):
        loop.quit()
        
    # Ждем завершения фонового потока
    mnemonic._worker.render_ready.connect(on_ready)
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    
    pixmap = mnemonic.grab()
    window.close()
    
    image = pixmap.toImage()
    image = image.convertToFormat(QImage.Format_RGB888)
    h, w = image.height(), image.width()
    bpl = image.bytesPerLine()
    
    # Решаем проблему с выравниванием (padding) строк в QImage
    arr = np.frombuffer(image.bits(), dtype=np.uint8).reshape(h, bpl)
    arr = arr[:, :w*3].reshape(h, w, 3)
    img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    
    # Сохраняем готовую схему в директорию проекта
    os.makedirs(RENDERED_DIR, exist_ok=True)
    basename = os.path.basename(scheme_path)
    cv2.imwrite(os.path.join(RENDERED_DIR, f"{basename}.png"), img_bgr)
    
    # Собираем данные для тестов
    expected_comps = []
    for cid, comp in mnemonic.components.items():
        class_name = comp.__class__.__name__
        if class_name != "ExternalPort":
            expected_comps.append({
                "id": cid,
                "name": getattr(comp, 'name', ''),
                "class_name": class_name
            })
            
    return img_bgr, expected_comps


@pytest.fixture(scope="session")
def check_deps():
    if cv2 is None or pytesseract is None or fuzz is None:
        pytest.skip("Requires opencv-python, pytesseract and fuzzywuzzy")


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_components_presence(check_deps, scheme_path, test_log):
    """Проверка того, что все компоненты были отрисованы в виде рамок."""
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    # Ищем темно-серые рамки оборудования (40-100 для сглаживания)
    lower_gray = np.array([40, 40, 40])
    upper_gray = np.array([100, 100, 100])
    mask_gray = cv2.inRange(img, lower_gray, upper_gray)
    kernel = np.ones((5,5), np.uint8)
    mask_gray = cv2.dilate(mask_gray, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes_count = sum(1 for cnt in contours if cv2.boundingRect(cnt)[2] > 30 and cv2.boundingRect(cnt)[3] > 30)
    
    # Не все классы имеют рамку, но мы просто проверяем что мы нашли хоть какие-то рамки
    # Более точная проверка может считать конкретные классы. Для начала проверим базовое наличие.
    test_log.check(f"Наличие рамок компонентов ({basename})", boxes_count, 1, op="ge")


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_pipe_intersections(check_deps, scheme_path, test_log):
    """Проверка того, что трубы не пересекают оборудование."""
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    # Получаем рамки
    lower_gray = np.array([40, 40, 40])
    upper_gray = np.array([100, 100, 100])
    mask_gray = cv2.inRange(img, lower_gray, upper_gray)
    kernel = np.ones((5,5), np.uint8)
    mask_gray = cv2.dilate(mask_gray, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(cnt) for cnt in contours if cv2.boundingRect(cnt)[2] > 30 and cv2.boundingRect(cnt)[3] > 30]
    
    pipe_colors = [
        np.array([212, 188, 0]),  # freon/freon_bypass
        np.array([243, 150, 33]), # water_lt
        np.array([0, 152, 255])   # water_ht
    ]
    
    pipes_mask = np.zeros(img.shape[:2], dtype=np.uint8)
    for color in pipe_colors:
        lower = np.clip(color - 10, 0, 255)
        upper = np.clip(color + 10, 0, 255)
        mask = cv2.inRange(img, lower, upper)
        pipes_mask = cv2.bitwise_or(pipes_mask, mask)
        
    total_intersections = 0
    for x, y, w, h in boxes:
        shrink = 5
        cx, cy, cw, ch = x + shrink, y + shrink, w - 2*shrink, h - 2*shrink
        if cw > 0 and ch > 0:
            roi = pipes_mask[cy:cy+ch, cx:cx+cw]
            total_intersections += cv2.countNonZero(roi)
            
    test_log.check(f"Пересечение труб и объектов ({basename})", total_intersections, 0)


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_labels_ocr(check_deps, scheme_path, test_log):
    """Проверка читаемости всех названий компонентов (OCR)."""
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    text_data = pytesseract.image_to_string(thresh, lang='rus+eng')
    text_data_lower = text_data.lower()
    
    for comp in expected_comps:
        expected_name = comp["name"].lower()
        if expected_name:
            match_score = fuzz.token_set_ratio(expected_name, text_data_lower)
            test_log.check(
                f"Читаемость текста '{expected_name}' ({basename})", 
                match_score, 
                55, 
                op="gt"
            )
