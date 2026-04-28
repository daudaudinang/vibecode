# Phase Notes Template

## Metadata

- phase_id: PXX
- status: pending | in_progress | waiting_user | completed | failed | cancelled
- current_step: <step>
- retry_count: <n>
- state_version: <n>

> Các field trên là mirror từ SQLite; authority thuộc `state_manager.py`.

## Decisions (authoritative)

- Quyết định đã chốt trong phase này

## Debt / Risks

- Nợ kỹ thuật phát sinh
- Risk còn mở

## Notes for Later Phases

- Context cần truyền cho phases phụ thuộc trực tiếp
