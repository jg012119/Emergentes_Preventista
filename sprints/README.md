# 📋 Plan de Sprints — Preventista Inteligente AJE

## Visión general

El desarrollo del MVP se organiza en **5 sprints** secuenciales. Cada sprint produce un entregable funcional, verificable y presentable.

---

## Resumen de sprints

| Sprint | Nombre | Objetivo principal | Duración estimada |
|---|---|---|---|
| **Sprint 1** | Sistema base completo | Backend, BD, app móvil y panel web SIN interpretación NLP ni voz | 1 semana |
| **Sprint 2** | Chat con lenguaje natural (texto) | Implementar procesamiento de texto para pedidos en el chat | 1 semana |
| **Sprint 3** | Reconocimiento de voz | Integrar voz → texto en la app móvil conectado al NLP | 1 semana |
| **Sprint 4** | Pruebas completas | Pruebas unitarias, integración, usabilidad y aceptación | 1 semana |
| **Sprint 5** | Reportes de aceptación | Reportes de aceptación del cliente, métricas y presentación final | 1 semana |

---

## Flujo de valor incremental

```text
Sprint 1                Sprint 2              Sprint 3              Sprint 4             Sprint 5
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────────┐     ┌──────────────┐
│ Sistema base │ ──►  │ Chat NLP     │ ──►  │ Voz → Texto  │ ──►  │ Pruebas     │ ──► │ Reportes     │
│ completo     │      │ (texto)      │      │ → NLP        │      │ completas   │     │ aceptación   │
└──────────────┘      └──────────────┘      └──────────────┘      └─────────────┘     └──────────────┘
```

---

## Estructura de carpetas

```
sprints/
├── README.md                    ← Este archivo
├── sprint-1/
│   ├── README.md                ← Descripción y objetivos del sprint
│   ├── backlog.md               ← User stories y tareas detalladas
│   ├── criterios_aceptacion.md  ← Criterios para dar por completado
│   └── entregables.md           ← Productos finales esperados
├── sprint-2/
│   ├── README.md
│   ├── backlog.md
│   ├── criterios_aceptacion.md
│   └── entregables.md
├── sprint-3/
│   ├── README.md
│   ├── backlog.md
│   ├── criterios_aceptacion.md
│   └── entregables.md
├── sprint-4/
│   ├── README.md
│   ├── backlog.md
│   ├── criterios_aceptacion.md
│   └── entregables.md
└── sprint-5/
    ├── README.md
    ├── backlog.md
    ├── criterios_aceptacion.md
    └── entregables.md
```

---

## Responsables por sprint

| Sprint | Responsable principal | Apoyo |
|---|---|---|
| Sprint 1 | Todo el equipo | — |
| Sprint 2 | Luz Laredo | Jairo, Valentina |
| Sprint 3 | Valentina Trigo | Jairo, Luz |
| Sprint 4 | Todo el equipo | — |
| Sprint 5 | Todo el equipo | — |

---

## Reglas generales

1. Cada sprint debe terminar con un **producto funcional verificable**.
2. No se avanza al siguiente sprint sin cerrar el anterior.
3. Las dudas se agrupan por sprint para consultas con la stakeholder.
4. Máximo **10 interacciones formales** con la stakeholder en total.
5. Cualquier cambio de alcance debe ser evaluado contra la viabilidad del mes de desarrollo.
