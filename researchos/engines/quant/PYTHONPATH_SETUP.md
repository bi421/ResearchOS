# cpp_quant_engine Python path setup

Энэ package нь sys.path-д автоматаар нэмэгддэггүй тул шинэ орчин/компьютер дээр
дараах алхмыг гүйцэтгэх шаардлагатай:

    python -c "import site; open(site.getsitepackages()[0] + '\cpp_quant_engine.pth', 'w').write(r'C:\Users\User\Desktop\ResearchOS\cpp_quant_engine\python')"

Эсвэл шууд: cpp_quant_engine.pth файлыг site-packages рүү хуулж, дотор нь
cpp_quant_engine/python-ийн бүтэн замыг бичих.

Энэ бол 2026-08-19-ний өдөр олдсон bug: researchos/quant_engine/cpp_backend.py
дотор "from cpp_quant_engine.cpp_quant_backend import (...)" гэж absolute import
хийдэг ч, sys.path-руу зам нэмэх ямар ч логик код дотор байхгүй байсан тул
PythonQuantBackend руу чимээгүйгээр fallback хийж байсан.
