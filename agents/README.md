# 🤖 Агенты

## Структура

- `core/` — Базовые агенты (сборщики, анализаторы, критики)
- `evolved/` — Эволюционировавшие агенты (потомки базовых)
- `variants/` — A/B тесты и экспериментальные версии

## Жизненный цикл агента

```
core/base → evolved/v1 → evolved/v2 → tested → [validated или retired]
```

## Формат описания агента

Каждый агент — YAML-файл с:
- `name` — имя
- `version` — семантическая версия
- `genome` — генетическая информация (родители, мутации, fitness)
- `capabilities` — что умеет
- `parameters` — настраиваемые параметры

## Пример: Генетический код

```yaml
genome:
  parent: [researcher-v2, critic-v1]
  mutations:
    - added: "self-reflection-loop"
    - removed: "verbose-output"
  fitness_score: 0.87
  lineage: [base, v1, v2, alpha-7]
```
