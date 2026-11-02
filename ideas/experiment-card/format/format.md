# Exp 01 — สำรวจพฤติกรรม Stage A/B/C

## คำถาม

เมื่อมีงบทำ intervention เท่ากัน ความไม่แน่นอนลดลงอย่างไรในแต่ละ Stage?

## สถานะ

Draft / Pilot / Frozen / Completed

## หน่วยที่ใช้เปรียบเทียบ

หนึ่ง hidden world = หนึ่งหน่วยหลัก
ถ้ารันหลาย policy seed บนโลกเดียวกัน ให้ถือเป็นการรันซ้ำภายในโลกนั้น

## ตัวแปรต้น (สิ่งที่เปลี่ยน)

- Stage: A, B, C
- Policy: ... [ถ้าจะเปลี่ยน policy ด้วย ให้ระบุว่าเป็นอีกปัจจัยหนึ่ง]

## ตัวแปรตาม (สิ่งที่วัด)

- หลัก: U_t = log2(จำนวน surviving worlds) หลังแต่ละ step
- รอง: final survivor count, realized information gain, action ที่เลือก

## ตัวแปรควบคุม (สิ่งที่ตรึง)

- Dataset: d=4, m=4
- Action budget: ...
- Hidden-world ชุดเดียวกันทุก condition
- Policy และ candidate limit: ...
- วิธีเลือก world และ seed schedule: ...

## Conditions

| ID  | Stage | Policy | Budget | Candidate limit |
| --- | ----- | ------ | -----: | --------------: |
| ... | ...   | ...    |    ... |             ... |

## จำนวนตัวอย่าง

- Pilot: ... hidden worlds เพื่อดู trace และตรวจวิธีบันทึกผล
- Main run: ยังไม่กำหนด; ใช้ Track 2 ประเมินความแม่นยำก่อน

## วิธีอ่านผล

- วาด U_t เทียบกับ step โดยแยก Stage
- เปรียบเทียบบน hidden worlds เดียวกัน
- Pilot ใช้ตั้งคำถามต่อ ห้ามสรุปว่า Stage ใดดีกว่าโดยทั่วไป

## สิ่งที่อาจทำให้ตีความผิด

- Stage มีจำนวนและชนิดของ action ต่างกัน
- ถ้าเปลี่ยน Stage และ policy พร้อมกัน จะบอกไม่ได้ว่าความต่างมาจากปัจจัยไหน
- หลาย step ใน episode เดียวกันไม่ใช่ตัวอย่างอิสระ

## สิ่งที่ผลนี้จะช่วยตัดสินใจ

...
