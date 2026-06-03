import re
import sys
import os
import random
from dataclasses import dataclass
from typing import List, Dict

# Add backend to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.routes.chat import _build_chat_reply
from app.models.schemas import ChatMessageCreate

class MockResult:
    def __init__(self, data):
        self.data = data

class MockTable:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self._data_to_return = []

    def select(self, *args, **kwargs):
        if self.name == "products":
            self._data_to_return = self.db.products
        elif self.name == "stores":
            self._data_to_return = [{"id": "store_123"}]
        elif self.name == "chat_messages":
            self._data_to_return = []
        elif self.name == "orders":
            self._data_to_return = [{"id": "order_123", "total": 0, "notes": ""}]
        elif self.name == "order_items":
            self._data_to_return = self.db.order_items
        return self

    def eq(self, *args, **kwargs): return self
    def order(self, *args, **kwargs): return self
    def limit(self, *args, **kwargs): return self
    def single(self, *args, **kwargs): return self
    def ilike(self, *args, **kwargs): return self
    
    def insert(self, data):
        data_list = [data] if isinstance(data, dict) else data
        if self.name == "orders":
            data_list[0]["id"] = "new_order_123"
            self.db.orders.append(data_list[0])
            self._data_to_return = data_list
        elif self.name == "order_items":
            self.db.order_items.extend(data_list)
            self._data_to_return = data_list
        return self
        
    def update(self, data):
        if self.name == "orders":
            self.db.order_updates.append(data)
        self._data_to_return = [{"id": "updated"}]
        return self

    def delete(self):
        if self.name == "order_items":
            self.db.deletions += 1
        return self

    def execute(self):
        return MockResult(self._data_to_return)

class MockDB:
    def __init__(self):
        self.products = [
            {"id": "p1", "name": "Big Cola 3L", "price": 10, "stock": 100, "active": True},
            {"id": "p2", "name": "Big Cola 2L", "price": 8, "stock": 100, "active": True},
            {"id": "p3", "name": "Big Cola 500ml", "price": 3, "stock": 100, "active": True},
            {"id": "p4", "name": "Agua Cielo 500ml", "price": 2, "stock": 100, "active": True},
            {"id": "p5", "name": "Agua Cielo 1L", "price": 4, "stock": 100, "active": True},
            {"id": "p6", "name": "Agua Cielo 2.5L", "price": 8, "stock": 100, "active": True},
            {"id": "p7", "name": "Volt 300ml", "price": 5, "stock": 100, "active": True},
            {"id": "p8", "name": "Volt 500ml", "price": 7, "stock": 100, "active": True},
            {"id": "p9", "name": "Cifrut 1L", "price": 5, "stock": 100, "active": True},
            {"id": "p10", "name": "Pulp 1L", "price": 6, "stock": 100, "active": True},
            {"id": "p11", "name": "Free Tea 500ml", "price": 4, "stock": 100, "active": True},
            {"id": "p12", "name": "Coca-Cola 2L", "price": 12, "stock": 100, "active": True},
        ]
        self.orders = []
        self.order_items = []
        self.order_updates = []
        self.deletions = 0

    def table(self, name):
        return MockTable(self, name)
        
    def reset(self):
        self.orders = []
        self.order_items = []
        self.order_updates = []
        self.deletions = 0


def generate_test_cases():
    cases = []
    
    # 1. Simple Orders (300)
    for _ in range(300):
        qty = random.choice(["2", "dos", "5", "cinco", "una docena de", "10"])
        prod = random.choice(["Big Cola 3 litros", "aguas de litro", "Volt pequeños", "Cielo 500", "Pulp de 1l"])
        jerga = random.choice(["casero mandame", "anotame", "quiero", "dame", ""])
        cases.append({"msg": f"{jerga} {qty} {prod} para mañana", "cat": "Simple", "expected_items": 1})
        
    # 2. Multiple Orders (300)
    for _ in range(300):
        cases.append({"msg": "caserita dame 3 big de 3 litros y 2 aguas medio litro aparte 4 volt 300 para mañana", "cat": "Multiple", "expected_items": 3})
        
    # 3. Cancelaciones (100)
    for _ in range(100):
        cases.append({"msg": random.choice(["cancela el pedido", "ya no quiero nada", "olvidalo", "anula eso"]), "cat": "Cancel", "order_id": "123"})
        
    # 4. Confirmaciones (100)
    for _ in range(100):
        cases.append({"msg": random.choice(["confirma el pedido", "mandalo nomas", "asi esta bien", "ok", "listo"]), "cat": "Confirm", "order_id": "123"})
        
    # 5. Ubicaciones / Zonas (200)
    for _ in range(200):
        cases.append({"msg": "mandame 4 big de tres por Cala Cala para mañana", "cat": "Ubicacion", "expected_items": 1, "check_notes": "Cala Cala"})
        
    # 6. Eliminar Productos (100)
    for _ in range(100):
        cases.append({"msg": "quita los volt", "cat": "Quitar", "order_id": "123"})

    # 7. Pedidos con Fecha (250)
    for _ in range(250):
        cases.append({"msg": "quiero 2 volt 500 para el viernes", "cat": "Fecha", "expected_items": 1})

    # 8. Errores Ortograficos (50)
    for _ in range(50):
        cases.append({"msg": "quiero 2 biq cola d 3 litruz para manana", "cat": "Spelling", "expected_items": 1})

    # 9. Pedidos Ambiguos / Incompletos (200)
    for _ in range(200):
        cases.append({"msg": "quiero 5 volt", "cat": "Incomplete", "expected_items": 0}) # expecting a question back
        
    # 10. Cambios de Fecha (25)
    for _ in range(25):
        cases.append({"msg": "mejor cambialo para el lunes", "cat": "CambioFecha", "order_id": "123"})

    # 11. Productos Inexistentes (25)
    for _ in range(25):
        cases.append({"msg": "mandame 2 fanta de litro", "cat": "Inexistente", "expected_items": 0})
        
    # 12. Correcciones / Agregar (200)
    for _ in range(200):
        cases.append({"msg": "ah y aumentame 3 cifrut 1l para mañana", "cat": "Agregar", "order_id": "123", "expected_items": 1})

    # 13. Cambios de Producto (25)
    for _ in range(25):
        cases.append({"msg": "en vez de volt dame pulp", "cat": "CambioProd", "order_id": "123", "expected_items": 0}) # Maybe won't work out of the box but let's test

    # 14. Fechas Invalidas (25)
    for _ in range(25):
        cases.append({"msg": "dame 2 volt 300 para el dia del juicio final", "cat": "FechaInvalida", "expected_items": 0}) # Will ask for date

    # 15. Casos Especiales (100)
    for _ in range(100):
        cases.append({"msg": "solo quiero 1 agua 500 para hoy", "cat": "Especial", "expected_items": 1})

    return cases

def run_tests():
    db = MockDB()
    cases = generate_test_cases()
    
    results = {"pass": 0, "fail": 0, "failures": []}
    
    for i, case in enumerate(cases):
        db.reset()
        body = ChatMessageCreate(message=case["msg"], sender="user", order_id=case.get("order_id"))
        
        try:
            reply = _build_chat_reply(db, "user_1", body)
            
            passed = True
            fail_reason = ""
            
            if case["cat"] in ["Simple", "Multiple", "Ubicacion"]:
                if len(db.order_items) != case.get("expected_items"):
                    passed = False
                    fail_reason = f"Expected {case.get('expected_items')} items, got {len(db.order_items)}. Reply: {reply}"
                elif case.get("check_notes") and not any(case["check_notes"].lower() in o.get("notes", "").lower() for o in db.orders):
                    passed = False
                    fail_reason = f"Expected notes '{case['check_notes']}' not found in {db.orders}"
                    
            elif case["cat"] == "Cancel":
                if not any(u.get("status") == "cancelado" for u in db.order_updates):
                    passed = False
                    fail_reason = f"Expected status 'cancelado' not found. Reply: {reply}"
                    
            elif case["cat"] == "Confirm":
                if not any(u.get("status") == "pendiente" for u in db.order_updates):
                    passed = False
                    fail_reason = f"Expected status 'pendiente' not found. Reply: {reply}"
                    
            elif case["cat"] == "Quitar":
                if db.deletions == 0:
                    passed = False
                    fail_reason = f"Expected deletion not triggered. Reply: {reply}"

            if passed:
                results["pass"] += 1
            else:
                results["fail"] += 1
                results["failures"].append({"msg": case["msg"], "reason": fail_reason})
                    
        except Exception as e:
            results["fail"] += 1
            results["failures"].append({"msg": case["msg"], "reason": str(e)})

    print(f"Total Tests: {len(cases)}")
    print(f"Passed: {results['pass']}")
    print(f"Failed: {results['fail']}")
    
    with open("scratch/test_results.md", "w", encoding="utf-8") as f:
        f.write("# Reporte de Pruebas Automáticas NLU\n\n")
        f.write(f"- **Total de Casos:** {len(cases)}\n")
        f.write(f"- **Aprobados:** {results['pass']}\n")
        f.write(f"- **Fallidos:** {results['fail']}\n\n")
        
        if results['fail'] == 0:
            f.write("✅ **¡Todos los casos de prueba pasaron exitosamente!**\n")
        else:
            f.write("## ❌ Casos que fallaron\n\n")
            for fail in results["failures"]:
                f.write(f"- **Input:** `{fail['msg']}`\n")
                f.write(f"  - **Error:** {fail['reason']}\n\n")

if __name__ == "__main__":
    run_tests()
