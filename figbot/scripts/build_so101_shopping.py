"""Reconcile the purchase ledger with one SO-101 follower; no CAD/robot actions."""
import csv
import hashlib
import io
import json
from decimal import Decimal
from scripts.project_paths import ROOT, SHOPPING, CURRENT, read_original


def load_data():
    plan = json.loads((ROOT / 'purchasing/so101_plan.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'purchasing/so101_inventory.json').read_text(encoding='utf-8'))
    return plan, inventory


def quantity(inventory, ids):
    return sum(r['quantity'] for r in inventory['rows'] if r['record_id'] in ids)


def disposition(record_id):
    if record_id == 69:
        return 'SİPARİŞ VERİLDİ', '6 motor; yeniden alım yok. Bedel, tam varyant ve teslim durumu TBD.'
    if record_id == 70:
        return 'SATIN ALINDI', '12 V 5 A masa adaptörü, 1 adet 321,25 TL. USB bus kartı değildir; fiş ve kutuplama kontrol edilecek.'
    if record_id == 67:
        return 'ELDE VAR', 'Önceki listedeki vidalar ve pirinç insertler; toplam 600 TL, kullanıcı beyanı. Ölçü başına kalan adet sayılmadı.'
    if record_id == 68:
        return 'ELDE VAR', 'Type-C kablo kullanıcıda var; veri aktarımı özelliği kontrol edilecek. Yeni alım yok, geçmiş fiyat bilinmiyor.'
    if record_id in {8, 14, 16, 21, 42, 44}:
        return 'MUHASEBE', 'Kargo/yuvarlama; fiziksel stok değildir.'
    if record_id in {3, 4, 10, 11}:
        return 'YEDEKTE KORU', 'PWM servo; standart SO-101 motoru yerine geçmez. Yardımcı mekanizmada ayrı değerlendirilir.'
    if record_id in {6, 7, 58, 59}:
        return 'YEDEKTE KORU', 'UNO/PCA9685/HC-05 bu kolun USB bus adaptörünün yerine geçmez.'
    if record_id == 1:
        return 'KOŞULLU KULLAN', 'Akü sağlığı ve mobil besleme yolu yük altında doğrulanacak; yeni akü şimdilik alma.'
    if record_id == 2:
        return 'KORU', 'Yalnız uygun aküyü şarj etmek için; 12 V regüle motor beslemesi değildir.'
    if record_id == 12:
        return 'KOŞULLU / YARDIMCI HAT', 'XL4016 yalnız düşürür; önceki gerilim çökmesi çözülmedi, 12 V kol kaynağı kabul edilmez.'
    if record_id == 13:
        return 'YEDEKTE KORU', 'INA219 3,2 A ölçüm kartı tüm kolun motor akımını taşımak için seçilmedi.'
    if record_id == 36:
        return '12 V HATTINDA KULLANMA', '4700 µF / 10 V; ancak uygun düşük gerilim hattında değerlendirilebilir.'
    if record_id in {22, 30, 39, 40, 41}:
        return 'KOŞULLU KULLAN', 'Anahtarlama/koruma devresi, soket ve sigorta değeri yeni güç yoluna göre doğrulanacak.'
    if record_id in {31, 32}:
        return 'YEDEKTE KORU', 'Eski PWM uzatma kablosu; STS3215 bus kablosuyla aynı kabul edilmez.'
    if record_id == 63:
        return 'STOK MİKTARI BELİRSİZ', 'Kısa PLA numune seti, tam makara değil; kalan gramaj ve baskı ihtiyacı ölçülecek.'
    if record_id in {5, 29, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 60, 61, 62, 64, 65}:
        return 'YEDEKTE KORU', 'Yardımcı elektronik/sensör sarfı; SO-101 temel kurulumunda yeni alımı yok.'
    return 'YENİDEN KULLAN', 'Alet veya montaj sarfı; sağlamlığı, uygun ölçüsü ve kalan miktarı kontrol edilerek kullanılır.'


def validate(plan, inventory, verify_source=True):
    rows = inventory['rows']
    assert len(rows) == 66 and sorted(r['record_id'] for r in rows) == list(range(1, 67))
    assert quantity(inventory, {3, 11}) == 7
    assert quantity(inventory, {4, 10}) == 2
    assert quantity(inventory, {7, 59}) == 2
    assert sum(Decimal(str(r['gross_try'])) for r in rows) == Decimal('8774.90')
    additional = inventory.get('user_records', [])
    assert len({r['record_id'] for r in rows + additional}) == len(rows + additional)
    for record in additional:
        assert record['gross_try'] is None or record['gross_try'] >= 0
    if verify_source:
        raw = read_original(ROOT / inventory['member'])
        assert hashlib.sha256(raw).hexdigest() == inventory['workbook_sha256']
    items = plan['items']
    assert len({x['id'] for x in items}) == len(items)
    assert items[0]['required'] == items[0]['ordered_quantity'] == 6
    assert items[0]['buy_min'] == items[0]['buy_max'] == 0
    assert items[2]['buy_min'] == items[2]['buy_max'] == 0
    for item in items:
        if 'order_record_id' in item:
            record = next(r for r in additional if r['record_id'] == item['order_record_id'])
            assert record['quantity'] == item['ordered_quantity']
            assert item['buy_max'] == max(0, item['required'] - item['ordered_quantity'])
    assert items[1]['required'] == items[1]['buy_min'] == items[1]['buy_max'] == 1
    for x in items:
        assert x['source'] in plan['sources']
        assert x['unit_price'] is None or x['unit_price'] > 0
        assert x['buy_max'] is None or 0 <= x['buy_min'] <= x['buy_max']
    for scenario in plan.get('supplier_scenarios', []):
        assert scenario['compatibility'] and scenario['package_complete'] is False
        for line in scenario['lines']:
            assert line['quantity'] > 0 and line['unit_price'] > 0
            assert line['currency'] in {'TRY', 'USD', 'EUR'}
            assert line['url'].startswith('https://')
    audit = plan['fastener_audit']
    for field, item_id in [('m2x6','N06'), ('m3x6','N07'), ('horns','N05')]:
        assert sum(r[field] for r in audit) == next(x['required'] for x in items if x['id'] == item_id)


def cost_estimate(plan, inventory):
    known = {}
    quoted = []
    unknown = []
    for item in plan['items']:
        if item['buy_max'] == 0:
            continue
        if item['unit_price'] is None or item['buy_min'] != item['buy_max']:
            unknown.append(item['id'])
            continue
        subtotal = Decimal(str(item['unit_price'])) * item['buy_min']
        known[item['currency']] = known.get(item['currency'], Decimal(0)) + subtotal
        quoted.append({'id':item['id'], 'quantity':item['buy_min'], 'subtotal':float(subtotal), 'currency':item['currency']})
    scenarios = []
    for scenario in plan.get('supplier_scenarios', []):
        totals = {}
        for line in scenario['lines']:
            currency = line['currency']
            totals[currency] = totals.get(currency, Decimal(0)) + Decimal(str(line['unit_price'])) * line['quantity']
        scenarios.append({**scenario, 'product_subtotals':{k:float(v) for k,v in totals.items()},
                          'delivered_total':None, 'complete':False})
    return {'revision':plan['revision'], 'checked_date':plan['checked_date'],
            'supplier_scenarios':scenarios,
            'priced_lines':quoted, 'known_partial_totals':{k:float(v) for k,v in known.items()},
            'unpriced_or_conditional_lines':unknown, 'complete':False, 'delivered_total':None,
            'shipping':None, 'import_costs':None, 'fx_rate':None,
            'historical_recorded_spend_try':float(sum(Decimal(str(r['gross_try'])) for r in inventory['rows'])),
            'user_reported_additions_try':float(sum(Decimal(str(r['gross_try'])) for r in inventory.get('user_records', []) if r['gross_try'] is not None)),
            'combined_recorded_spend_try':float(sum(Decimal(str(r['gross_try'])) for r in inventory['rows'] + inventory.get('user_records', []) if r['gross_try'] is not None)),
            'note':'Tarihsel harcama yeni alıma eklenmez; bilinmeyen maliyet sıfır değildir.'}


def cell(value):
    return str(value).replace('|','/').replace('\n',' ') if value is not None else 'TBD'


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] +
                     ['| '+' | '.join(cell(v) for v in row)+' |' for row in rows])


def buy_text(item):
    low, high = item['buy_min'], item['buy_max']
    return str(low) if low == high else f'{low}–{high if high is not None else "TBD"}'


def csv_text(headers, rows):
    s = io.StringIO(newline='')
    w = csv.writer(s, delimiter=';'); w.writerow(headers); w.writerows(rows)
    return s.getvalue()


def publish():
    plan, inventory = load_data()
    validate(plan, inventory)
    cost = cost_estimate(plan, inventory)
    sources = plan['sources']
    outputs = {}
    shopping_rows = [[x['id'], x['group'], x['item'], x['required'], buy_text(x), x['unit'],
                      x['unit_price'], x['currency'], sources[x['source']], x['note']] for x in plan['items']]
    headers = ['Kod','Durum','Malzeme','Toplam ihtiyaç','Yeni alım','Birim','Birim fiyat','Para birimi','Bağlantı','Açıklama']
    outputs['SO101_ALISVERIS_LISTESI.csv'] = csv_text(headers, shopping_rows)
    inv_rows = [[r['record_id'], r['item'], r['quantity'], r['status'], *disposition(r['record_id']),
                 r['gross_try'], r['supplier'], r['excel_row'], r['verification'], r['notes']] for r in inventory['rows'] + inventory.get('user_records', [])]
    outputs['SO101_MEVCUT_ALIMLAR.csv'] = csv_text(
        ['Kayıt','Ürün','Alınan adet','Kayıt durumu','Yeni plandaki karar','Açıklama','Geçmiş bedel TL','Satıcı','Excel satırı','Kaynak doğrulaması','Kaynak notu'], inv_rows)
    if inventory.get('user_records'):
        outputs['SO101_KULLANICI_ALIM_EKLERI.json'] = json.dumps(inventory['user_records'], ensure_ascii=False, indent=2)
    outputs['SO101_MALIYET.json'] = json.dumps(cost, ensure_ascii=False, indent=2)
    reuse_summary = [
        ['ORBUS 12 V 9 Ah akü', '1', 'Koşullu koru; önce besleme arızasını ayır', '1'],
        ['MERVESAN 12 V 2 A akü şarj cihazı', '1', 'Akü şarjında koru', '2'],
        ['MG996R / MG90S', '7 / 2', 'SO-101 motoru yerine kullanma; yardımcı işlere ayır', '3,11 / 4,10'],
        ['UNO / PCA9685 / HC-05', '1 / 2 / 1', 'Eski sistemi ve ileride yardımcı kontrolü koru', '6 / 7,59 / 58'],
        ['XL4016 / INA219', '2 / 2', 'Ana SO-101 beslemesinde doğrulanmış çözüm değil', '12 / 13'],
        ['14 AWG kırmızı / siyah silikon kablo', '2 m / 3 m', 'Güç bağlantısında eldeki kalan kabloyu kullan', '37 / 43'],
        ['XT60 erkek-dişi takımı', '2 takım', 'Güç hattında kullan', '17'],
        ['2 giriş / 6 çıkış dağıtım klemensi', '4 adet', 'Uygun akım ve kablo ölçüsü doğrulanarak kullan', '20,23'],
        ['Sigorta yuvası / 7,5 A ve 10 A sigorta', '3 / her birinden 3', 'Yuvaları koru; sigorta değeri ayrıca seçilecek', '40 / 39,41'],
        ['Acil durdurma / 12 V otomotiv rölesi', '1 / 1', 'Yeni güç devresinde bağlantısı doğrulanarak değerlendir', '22 / 30'],
        ['Multimetre / havya / kumpas', '1 / 1 / 1', 'Yeniden alım yok; kumpas adedi kaynakta varsayılmış', '9 / 15 / 66'],
        ['Makaron / kablo bağı / yüksük / pabuç', 'Çeşitli paketler', 'Önce mevcut stoğu kullan', '24–28,33–35,38'],
        ['4700 µF / 10 V kondansatör', '5', '12 V motor hattında kullanma', '36'],
        ['Bilgisayar ve 3D yazıcı', 'Konuşmada mevcut', 'Yeni alım yok; Excel harcamasına dahil edilmedi', 'Kullanıcı beyanı']
    ]
    intro = f'''# SO-101 — mevcut malzemeler ve yeni alım listesi

{plan['checked_date']} · {plan['revision']} · {plan['scope']}

**Güncel alım durumu:** 6 motor sipariş edildi; 1 adet 12 V 5 A masa adaptörü **321,25 TL** bedelle satın alındı. Bunları tekrar alma. Motor sipariş bedeli ve tam varyantı TBD. USB bus adaptör kartının alındığı bildirilmedi; güç adaptörü bu kartın yerine geçmez. Mevcut vidalar, kablolar ve aletler uygunluk kontrolüyle kullanılır.

Bu dosya SO-101 alım planıdır. Önceki LINKA alışveriş PDF'leri bu kola ait değildir. SO-101 baskı teslimi GUNCEL/BASKI/ONCE_BUNU_OKU.md ve GUNCEL/SURUM.json üzerinden izlenir. Eski motor kontrol yazılımı yeni bus servolarla uyumlu sayılmaz.

## Satın alma kaynağı

Arşiv: `{inventory['archive']}`; üye: `{inventory['member']}`; sayfa: `{inventory['sheet']}`. Çalışma kitabı SHA256: `{inventory['workbook_sha256']}`.

66 kayıt incelendi. “Satın Alındı” ile “Teslim Edildi” durumları korunur; miktarlar kalan fiziksel stok sayımı değildir. Eski plan/BOM önerileri satın alınmış kabul edilmedi. Satıcı/vergiler hakkında kaynakta bulunan UNVERIFIED notları CSV'de korunur. Geçmiş kayıt toplamı 8.774,90 TL'dir; kargo ve yuvarlama içerir, yeni alım bütçesine eklenmez.

Kullanıcı beyanları: vida ve pirinç insertler **600,00 TL**; masa adaptörü **321,25 TL**; altı motor siparişi **bedel TBD**. Bilinen kayıtlı harcama **{cost['combined_recorded_spend_try']:.2f} TL**; buna motorların bilinmeyen bedeli dahil değildir. Type-C kablo elde var, geçmiş fiyatı bilinmiyor. Arşiv Excel değiştirilmedi; ek kayıtlar güncel CSV ve SO101_KULLANICI_ALIM_EKLERI.json içindedir. Vida ölçüleri önceki listeden referanslanır, kalan adetler doğrulanmamıştır.

## Mevcut alımlardan yararlanma

{table(['Parça','Kayıtlı miktar','Karar','Excel kayıt no'],reuse_summary)}

Diğer küçük elektronik sarflar yeni alım gerektirmez. Kaynak 66 satır ve kullanıcı ekleri: **SO101_MEVCUT_ALIMLAR.csv**.

## Yeni alım ve yalnız eksikse tamamlanacaklar

'''
    blocks = []
    for group in dict.fromkeys(x['group'] for x in plan['items']):
        rows = []
        for x in plan['items']:
            if x['group'] != group: continue
            price = f"{x['unit_price']:.2f} {x['currency']}" if x['unit_price'] is not None else 'TBD'
            rows.append([x['id'], x['item'], f"{cell(x['required'])} {x['unit']}", buy_text(x), price,
                         f"[Ürün / teknik kaynak]({sources[x['source']]})",x['note']])
        blocks += ['### '+group, table(['Kod','Parça','Toplam ihtiyaç','Alınacak','Birim fiyat','Kaynak','Not'],rows)]
    end = f'''

## Motor paketini kontrol et — tekrar satın alma

Satıcıya: “Bir SO-101 follower kuracağım. Altı adet STS3215-C047, 12 V, 1:345 istiyorum. SO-101'e uygun ön/arka başlıkları, bus kabloları ve M2×6/M3×6 montaj vidaları paketlere dahil mi? Her aksesuarın adet ve fotoğrafını teyit eder misiniz?”

Motorun ticari paket içeriği kesinleştirilmedi. Başlık ve kabloyu ayrı sipariş vermeden önce motor paketini kontrol et. Mekanik kılavuzdan sayılan ihtiyaçlar aşağıdadır; kart/masa/araç bağlantı sarfı bu sayıların dışındadır. [Montaj kaynağı]({sources['assembly']}).

{table(['Eklem','M2×6','M3×6','Başlık'],[[r['joint'],r['m2x6'],r['m3x6'],r['horns']] for r in plan['fastener_audit']])}

Toplam **24 M2×6, 50 M3×6 ve 11 başlık**. Hiç yoksa yedekli 30 / 60 vida ve 6 çift başlık takımı alınır; paket içeriği ve mevcut stok düşülür. Rastgele insert, ilave rulman veya tornacı işi siparişi yok.

## Maliyet

- Altı motor sipariş edildi; ödenen bedel **TBD**. Eski 143,94 USD ürün teklifi gerçekleşen alım tutarı değildir.
- 1 × 4,99 USD adaptör kartı = **4,99 USD**. [Kart fiyat kaynağı]({sources['board']}).
- Kalan sabit adetli, fiyatı bulunan yeni alım: **{cost['known_partial_totals']}**. Bu tutar tamamlanmış veya Türkiye'ye teslim maliyeti değildir.
- Güç adaptörü satın alındı: **321,25 TL**. Geçmiş 319,83 TL teklifin yerini kullanıcı tarafından bildirilen gerçek bedel aldı. Satıcı belirtilmedi; ürün bağlantısı önceki adaydır, sipariş kanıtı değildir.
- Varsa eksik aksesuarlar/filament, kargo ve vergiler: **TBD**. Bilinmeyen bedeller sıfır sayılmadı. Hesap: SO101_MALIYET.json.

Yerel güç kaynağı taramasında bulunan ST-A0060AAL'nin GX-12 fişi kartın DC5521 girişine doğrudan uymaz; 60 W diğer ürün de stok dışı ve DC5525 uçluydu. Sırf 12 V / 5 A yazıyor diye bu ürünleri doğrudan satın alma satırına koymadık. Doğru fiş/polarite veya klemens kablosuyla uyum netleşmeli.

## Kapsam ve açık teknik noktalar

'''
    end += '\n\n'.join('- '+n for n in plan['notes'])
    end += '\n\nTeknik kaynaklar: '+', '.join(f'[{k}]({sources[k]})' for k in ['upstream','datasheet','board_limits','board_spec'])+'.\n'
    supplier_section = ''
    if plan.get('supplier_comparison_markdown'):
        supplier_section = (ROOT / plan['supplier_comparison_markdown']).read_text(encoding='utf-8')
        outputs['SO101_TEDARIKCI_KARSILASTIRMASI.md'] = supplier_section
        supplier_section = '\n## Önceki tedarik araştırması — sipariş tutarı değildir\n\nMotorlar ve güç adaptörü artık sipariş/satın alma kaydındadır. Aşağıdaki önceki fiyatlar tekrar alım talebi değildir.\n\n' + supplier_section + '\n\n---\n\n'
    outputs['SO101_ALISVERIS_LISTESI.md'] = intro + supplier_section + '\n\n'.join(blocks) + end
    outputs['SO101_DOGRULAMA.json'] = json.dumps({'revision':plan['revision'], 'inventory_rows':66,
        'user_record_count':len(inventory.get('user_records', [])),
        'source_sha256_verified':True,'inventory_totals':{'MG996R':7,'MG90S':2,'PCA9685':2},
        'ordered_servos':6,'new_servos':0,'purchased_power_adapters':1,'new_usb_adapters':1,'cost_complete':False,'physical_approval':False}, indent=2)
    SHOPPING.mkdir(parents=True, exist_ok=True)
    # Preserve earlier revisions of only these deliverables, not unrelated CAD/print files.
    from scripts.project_paths import ARCHIVE
    from datetime import datetime, timezone
    import zipfile
    changed = [SHOPPING/name for name,text in outputs.items() if (SHOPPING/name).exists()
               and (SHOPPING/name).read_bytes() != text.encode('utf-8-sig' if name.endswith('.csv') else 'utf-8')]
    if changed:
        prefix = 'SO101_ALISVERIS_ONCEKI/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
        with zipfile.ZipFile(ARCHIVE,'a',compression=zipfile.ZIP_DEFLATED) as z:
            for p in changed: z.write(p,prefix+p.name)
        with zipfile.ZipFile(ARCHIVE) as z:
            for p in changed:
                assert hashlib.sha256(z.read(prefix+p.name)).digest() == hashlib.sha256(p.read_bytes()).digest()
    for name,text in outputs.items():
        (SHOPPING/name).write_bytes(text.encode('utf-8-sig' if name.endswith('.csv') else 'utf-8'))
    records=[{'path':p.relative_to(CURRENT).as_posix(),'bytes':p.stat().st_size,
              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json']
    (CURRENT/'DOSYA_LISTESI.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps({'published':list(outputs),'partial_cost':cost['known_partial_totals'],'physical_approval':False}))


if __name__ == '__main__':
    publish()
