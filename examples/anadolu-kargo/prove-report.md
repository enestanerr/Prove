# Prove report — examples/anadolu-kargo/report.md

**3 contradicted · 0 suspect · 0 unverified · 7 verified**

- computed: 2 contradicted, 6 verified
- read from a chart or image: 1 contradicted, 1 verified

Numeric statements found: 26   checked: 21   skipped with reason: 5   missed: 0

## Contradicted (3)

**c2 · computed · page 1**
> Teslim edilen gönderi sayısı 1.284.500'den 1.412.920'ye çıktı; bu %12 artış demek.
Gönderi artışı, 1.284.500'den 1.412.920'ye değişim olmalı.
`1.412.920 ÷ 1.284.500 − 1 = 10.00%; the document says %12`
No rounding of the printed numbers can produce this figure.

**c6 · computed · page 2**
> Marmara, toplam gönderilerin %38,3'ünü oluşturdu.
Marmara'nın payı, Marmara gönderilerinin dört bölge toplamına oranı olmalı.
`512,4 ÷ (512,4 + 318,7 + 271,3 + 310,5) = 36.27%; possible range 36.26%–36.27%; the document says %38,3`
No rounding of the printed numbers can produce this figure.

**c7 · read from a chart or image · Şekil 1 · page 2**
> Eylül ayında 520 bin gönderiyle çeyreğin en yüksek aylık değerine ulaşıldı.
Metindeki Eylül gönderi sayısı, Şekil 1'deki Eylül çubuğuyla uyuşmalı.
`the Eylül bar in Şekil 1 reads 485–495 (first reading 485–495, second reading 487–493); the document says 520`
The chart reading and the printed number cannot both be right.
Chart note: Dikey eksen sıfırdan değil 400'den başlıyor; çubuklar arasındaki fark olduğundan büyük görünür.

## Verified (7)

**c1 · computed · page 1**
> Gelir 2. çeyrekteki 48,6 milyon TL'den 3. çeyrekte 53,9 milyon TL'ye yükseldi; artış %10,9.
Gelir artışı, 48,6 milyondan 53,9 milyona değişim olmalı.
`53,9 milyon ÷ 48,6 milyon − 1 = 10.91%; possible range 10.69%–11.12%; the document says %10,9`
Recomputing from the printed numbers gives the printed figure.

**c3 · computed · page 1**
> Zamanında teslimat oranı %94,2'den %96,0'a yükseldi; 1,8 puanlık bir iyileşme.
İyileşme, %96,0 ile %94,2 arasındaki puan farkı olmalı.
`%96,0 − %94,2 = 1.80 pp; possible range 1.70 pp–1.90 pp; the document says 1,8 pp`
Recomputing from the printed numbers gives the printed figure.

**c4 · computed · page 2**
> Toplam | 1.412,9
Toplam satırı dört bölgenin toplamı olmalı.
`512,4 + 318,7 + 271,3 + 310,5 = 1,412.9; possible range 1,412.7–1,413.1; the document says 1.412,9`
Recomputing from the printed numbers gives the printed figure.

**c5 · computed · page 1**
> Teslim edilen gönderi sayısı 1.284.500'den 1.412.920'ye çıktı; bu %12 artış demek.
Özetteki gönderi sayısı, tablodaki toplamla aynı olmalı.
`printed as 1.412,9 elsewhere; the document says 1.412.920`
Recomputing from the printed numbers gives the printed figure.

**c8 · read from a chart or image · Şekil 1 · page 2**
Eylül çubuğu, Şekil 1'deki en yüksek çubuk olmalı.
`the Eylül bar in Şekil 1 reads 485–495; the others read Temmuz 450–460, Ağustos 463–473; the document calls Eylül the largest`
The chart readings do not contradict the stated order.
Chart note: Dikey eksen sıfırdan değil 400'den başlıyor; çubuklar arasındaki fark olduğundan büyük görünür.

**c9 · computed · page 3**
> Filo 420 araçtan oluşuyor; bunların 124'ü, yani yaklaşık %30'u elektrikli.
Elektrikli araç payı, 124'ün 420'ye oranı olmalı.
`124 ÷ 420 = 29.52%; the document says about %30`
Recomputing from the printed numbers gives the printed figure.

**c10 · computed · page 3**
> 92 günlük çeyrekte araç başına günde ortalama 36,6 teslimat yapıldı.
Araç başına günlük teslimat, gönderi sayısının araç sayısı ile gün sayısının çarpımına bölümü olmalı.
`1.412.920 ÷ (420 × 92) = 36.566; the document says 36,6`
Recomputing from the printed numbers gives the printed figure.

---
A clean report means the checked claims passed. It does not mean the document is right: see the coverage line for how many numeric statements were checked. Prove does not judge opinions, forecasts or strategy, and it does not know whether a source is correct, only whether it exists and says what is quoted.

Verdicts computed by provecheck 0.1.0.
