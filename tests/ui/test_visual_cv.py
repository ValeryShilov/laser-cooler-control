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
    if os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pytesseract = None

try:
    import easyocr
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    OCR_READER = easyocr.Reader(['en', 'ru'], gpu=False)
except ImportError:
    OCR_READER = None

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
    
    # Принудительно вызываем layout, чтобы у компонентов появились x, y, w, h
    mnemonic.layout_engine.layout(mnemonic.components, mnemonic.connections)
    
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
    
    # Учитываем масштабирование на High DPI мониторах (например, 1.25)
    dpr = mnemonic.devicePixelRatio()
    
    # Собираем данные для тестов
    expected_comps = []
    for cid, comp in mnemonic.components.items():
        class_name = comp.__class__.__name__
        if class_name != "ExternalPort":
            expected_comps.append({
                "id": cid,
                "name": getattr(comp, 'name', ''),
                "class_name": class_name,
                "x": int(comp.x * dpr),
                "y": int(comp.y * dpr),
                "w": int(comp.width * dpr),
                "h": int(comp.height * dpr),
                "label_pos": getattr(comp, 'label_pos', 'bottom')
            })
            
    return img_bgr, expected_comps


@pytest.fixture(scope="session")
def check_deps():
    if cv2 is None or pytesseract is None or fuzz is None:
        pytest.skip("Requires opencv-python, pytesseract and fuzzywuzzy")


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_components_presence(check_deps, scheme_path, test_log):
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Находим все контуры на всем изображении (вне зависимости от цвета, ищем просто линии)
    edges = cv2.Canny(gray, 30, 150)
    
    found_count = 0
    for comp in expected_comps:
        x, y, w, h = comp['x'], comp['y'], comp['w'], comp['h']
        
        # Защита от выхода за границы изображения
        if x < 0 or y < 0 or x+w > edges.shape[1] or y+h > edges.shape[0]:
            continue
            
        # Берем кусок (ROI) из карты граней Кенни, где должен быть расположен компонент
        roi_edges = edges[y:y+h, x:x+w]
        
        # Если в этой зоне есть хотя бы несколько пикселей граней (контуров)
        # значит компонент (его SVG графика) был физически нарисован на холсте!
        edge_pixels = cv2.countNonZero(roi_edges)
        print(f"DEBUG: {basename} | Comp {comp['id']} ({comp['class_name']}) at x={x}, y={y}, w={w}, h={h} | Edge Pixels: {edge_pixels}")
        
        if edge_pixels > 20: # 20 пикселей это надежный минимум для SVG иконки
            found_count += 1
            
    # Проверяем, что компоненты физически не накладываются друг на друга
    overlap_count = 0
    for i in range(len(expected_comps)):
        for j in range(i + 1, len(expected_comps)):
            c1, c2 = expected_comps[i], expected_comps[j]
            x_left = max(c1['x'], c2['x'])
            y_top = max(c1['y'], c2['y'])
            x_right = min(c1['x'] + c1['w'], c2['x'] + c2['w'])
            y_bottom = min(c1['y'] + c1['h'], c2['y'] + c2['h'])
            
            if x_right > x_left and y_bottom > y_top:
                overlap_count += 1
                
    test_log.check(f"Наложение компонентов ({basename})", overlap_count, 0, op="eq")
    
    # Проверяем, что количество найденных графических блоков совпадает с количеством в YAML
    test_log.check(f"Все компоненты отрисованы ({basename})", found_count, len(expected_comps), op="eq")


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_pipe_intersections(check_deps, scheme_path, test_log):
    """Проверка того, что трубы не пересекают оборудование (внутреннюю часть)."""
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    # Так как мы не запускаем систему (is_running=False), все трубы рисуются серым цветом
    pipe_colors = [
        np.array([180, 180, 180]) # idle_c
    ]
    
    pipes_mask = np.zeros(img.shape[:2], dtype=np.uint8)
    for color in pipe_colors:
        lower = np.clip(color - 10, 0, 255)
        upper = np.clip(color + 10, 0, 255)
        mask = cv2.inRange(img, lower, upper)
        pipes_mask = cv2.bitwise_or(pipes_mask, mask)
        
    total_intersections = 0
    for comp in expected_comps:
        x, y, w, h = comp['x'], comp['y'], comp['w'], comp['h']
        
        # Сужаем рамку на 5 пикселей со всех сторон (или 6 с учетом DPR), 
        # чтобы игнорировать трубы, которые легально подходят к портам по краям.
        shrink = int(5 * getattr(img, 'dpr', 1.25)) # Приблизительное сужение
        cx, cy, cw, ch = x + shrink, y + shrink, w - 2*shrink, h - 2*shrink
        
        if cw > 0 and ch > 0 and cx >= 0 and cy >= 0 and cx+cw <= img.shape[1] and cy+ch <= img.shape[0]:
            roi = pipes_mask[cy:cy+ch, cx:cx+cw]
            intersecting_pixels = cv2.countNonZero(roi)
            if intersecting_pixels > 10: # Допуск на мелкие артефакты сглаживания
                total_intersections += intersecting_pixels
            
    test_log.check(f"Пересечение труб и объектов ({basename})", total_intersections, 0)


@pytest.mark.parametrize("scheme_path", SCHEME_FILES)
def test_cv_labels_ocr(check_deps, scheme_path, test_log):
    """Проверка читаемости текста (названия компонентов) через EasyOCR."""
    if OCR_READER is None:
        pytest.skip("EasyOCR не установлен")
        
    img, expected_comps = get_rendered_data(scheme_path)
    basename = os.path.basename(scheme_path)
    
    # EasyOCR лучше работает с контрастными изображениями, 
    # но он и сам неплохо справляется с цветным текстом.
    # Мы можем просто передать ему весь BGR-кадр.
    results = OCR_READER.readtext(img)
    
    # Собираем весь найденный текст в единую строку для нечеткого поиска
    text_data_lower = " ".join([text.lower() for (bbox, text, prob) in results])
    
    for comp in expected_comps:
        expected_name = comp["name"].lower()
        if expected_name:
            match_score = fuzz.token_set_ratio(expected_name, text_data_lower)
            test_log.check(
                f"Читаемость текста '{expected_name}' ({basename})", 
                match_score, 
                60, 
                op="gt"
            )
