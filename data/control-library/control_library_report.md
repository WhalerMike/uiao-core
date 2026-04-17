# uiao-core Control Library Report

Generated: 2026-04-16

**Total files**: 247
**Base controls**: 163
**Enhancements**: 84
**Granular controls**: 247

## Family Breakdown
- **AC**: 25 files (base=18, enh=7, ksi-linked=25)
- **AT**: 6 files (base=4, enh=2, ksi-linked=6)
- **AU**: 18 files (base=12, enh=6, ksi-linked=18)
- **CA**: 11 files (base=8, enh=3, ksi-linked=11)
- **CM**: 19 files (base=11, enh=8, ksi-linked=19)
- **CP**: 15 files (base=9, enh=6, ksi-linked=15)
- **IA**: 22 files (base=10, enh=12, ksi-linked=22)
- **IR**: 12 files (base=8, enh=4, ksi-linked=12)
- **MA**: 9 files (base=5, enh=4, ksi-linked=9)
- **MP**: 8 files (base=7, enh=1, ksi-linked=8)
- **PE**: 18 files (base=16, enh=2, ksi-linked=18)
- **PL**: 6 files (base=5, enh=1, ksi-linked=6)
- **PS**: 9 files (base=9, enh=0, ksi-linked=9)
- **RA**: 10 files (base=6, enh=4, ksi-linked=10)
- **SA**: 18 files (base=11, enh=7, ksi-linked=18)
- **SC**: 22 files (base=14, enh=8, ksi-linked=22)
- **SI**: 19 files (base=10, enh=9, ksi-linked=19)

## Quality Metrics
- KSI coverage: **247** / 247 files (100.0%)
- Parameters: **215** files
- Implementation statements: **218** files

## Priority-family KSI coverage (AC/SC/IA/AU/CM)

- Linked: **106** / 106 (100.0%)
- SCuBA-importer threshold: 80%
- Status: **READY**

## Next Steps
- Full-tree KSI coverage achieved — every control file carries a canonical `ksi:` pointer.
- Keep `tools/link_ksi_to_controls.py --check-only` in CI to prevent regression as new controls land.
