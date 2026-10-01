# Rev-I — mevcut motorlarla doğrudan yan sepete

Durum: **CAD YERLEŞİM İNCELEMESİ — BASKIYA HAZIR DEĞİL**.

Aktif yön DEC-068: teker önünde kısa kol; sağa-sola dönüş; teker üstünden başlayan yan giriş; bant yok. İki kol konumu mimariyi gösterir, satın alınmış iki takım motor iddiası değildir.

![Yerleşim kesiti](layout_section.png)

Kaynak: ../build_rev_i_direct_basket.py. Gerekçe ve tüm sınırlamalar: ../../../reports/20260911_REV_I_DIRECT_BASKET_TR.md.

STEP ve GLB iki pozu gösterir. URDF sabit inceleme içindir, kontrol/fizik modeli değildir. REVIEW.json fiziksel test sonucu değildir. Üç parmak aktarması, bağlantı toleransları, iç çakışmalar, yük altında tork/mukavemet ve gerçek servo kalibrasyonu açık konulardır. Bu klasördeki inceleme STL'lerini üretim parçası gibi basmayın.

Yeniden üretim: `.venv/Scripts/python.exe -m cad.rover.build_rev_i_direct_basket`

Kontrol: `.venv/Scripts/python.exe -m pytest tests/test_rev_i_direct_basket.py -q`
