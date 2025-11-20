import streamlit as st
from sqlalchemy.orm import Session
from db import SessionLocal, init_db
from models import Base, Supplier, Product, Inventory, PurchaseOrder, POItem
import pandas as pd
from datetime import datetime

# Initialize DB
init_db(Base)

st.set_page_config(page_title="Supply Chain Manager", layout="wide")
st.title("Supply Chain Manager — Minimal MVP")
st.markdown("Manage suppliers, products, inventory and purchase orders.")

# Helper to get a DB session
def get_session():
    return SessionLocal()

# Navigation helper to change page safely from callbacks
def navigate(page_name: str):
    st.session_state['page'] = page_name

# Sidebar navigation (use session state key so we can change it programmatically)
st.sidebar.selectbox("Page", ["Dashboard", "Suppliers", "Products", "Inventory", "Purchase Orders"], key="page")
# Ensure a default page key exists in session state
if 'page' not in st.session_state:
    st.session_state['page'] = 'Dashboard'
page = st.session_state.get("page", "Dashboard")

if page == "Dashboard":
    st.header("Overview")
    with get_session() as s:
        total_products = s.query(Product).count()
        total_suppliers = s.query(Supplier).count()
        low_stock = s.query(Inventory).filter(Inventory.qty_on_hand <= Inventory.reorder_point).count()
    # Clickable metrics: clicking a number will navigate to the corresponding page
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button(str(total_products), key="metric_products", on_click=navigate, args=("Products",))
        st.caption("Products")
    with c2:
        st.button(str(total_suppliers), key="metric_suppliers", on_click=navigate, args=("Suppliers",))
        st.caption("Suppliers")
    with c3:
        st.button(str(low_stock), key="metric_low_stock", on_click=navigate, args=("Inventory",))
        st.caption("Low stock SKUs")
    st.markdown("---")
    st.subheader("Recent Purchase Orders")
    with get_session() as s:
        pos = s.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(10).all()
    for po in pos:
        st.write(f"PO {po.po_number} — {po.supplier.name if po.supplier else 'Unknown'} — Received: {po.received}")

elif page == "Suppliers":
    st.header("Suppliers")
    with get_session() as s:
        suppliers = s.query(Supplier).order_by(Supplier.name).all()
    cols = st.columns([1,3,1,1,1])
    for sup in suppliers:
        st.write(f"**ID {sup.id} — {sup.name}** — {sup.contact or ''}")
        st.write(f"{sup.email or ''} • {sup.phone or ''}")
        st.markdown('---')
    st.subheader("Add Supplier")
    with st.form("add_supplier"):
        name = st.text_input("Name")
        contact = st.text_input("Contact")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        submitted = st.form_submit_button("Add")
        if submitted:
            with get_session() as s:
                sup = Supplier(name=name, contact=contact, email=email, phone=phone)
                s.add(sup)
                s.commit()
            st.success(f"Supplier added — ID: {sup.id}")

elif page == "Products":
    st.header("Products")
    with get_session() as s:
        products = s.query(Product).order_by(Product.name).all()
    for p in products:
        st.write(f"**{p.sku} — {p.name}** (Supplier: {p.supplier.name if p.supplier else '—'})")
        st.write(f"Unit cost: {p.unit_cost}")
        st.markdown('---')
    st.subheader("Add Product")
    with st.form("add_product"):
        sku = st.text_input("SKU")
        name = st.text_input("Name")
        desc = st.text_area("Description")
        unit_cost = st.number_input("Unit cost", value=0.0, format="%.2f")
        supplier_id = st.number_input("Supplier ID (optional)", value=0)
        submitted = st.form_submit_button("Add product")
        if submitted:
            with get_session() as s:
                p = Product(sku=sku, name=name, description=desc, unit_cost=unit_cost)
                if supplier_id:
                    p.supplier_id = int(supplier_id)
                s.add(p)
                s.commit()
            st.success("Product added")

elif page == "Inventory":
    st.header("Inventory")
    with get_session() as s:
        inv = s.query(Inventory).join(Product).all()
    df = pd.DataFrame([{
        'product': i.product.name if i.product else '',
        'sku': i.product.sku if i.product else '',
        'qty_on_hand': i.qty_on_hand,
        'reorder_point': i.reorder_point
    } for i in inv])
    st.dataframe(df)
    st.subheader("Adjust Inventory")
    with st.form("adjust"):
        sku = st.text_input("Product SKU")
        qty = st.number_input("New qty on hand", value=0)
        reorder = st.number_input("Reorder point", value=10)
        submitted = st.form_submit_button("Update")
        if submitted:
            with get_session() as s:
                p = s.query(Product).filter(Product.sku == sku).first()
                if not p:
                    st.error("Product not found")
                else:
                    if not p.inventory:
                        inv = Inventory(product_id=p.id, qty_on_hand=qty, reorder_point=reorder)
                        s.add(inv)
                    else:
                        p.inventory.qty_on_hand = int(qty)
                        p.inventory.reorder_point = int(reorder)
                        p.inventory.last_updated = datetime.utcnow()
                    s.commit()
                    st.success("Inventory updated")

elif page == "Purchase Orders":
    st.header("Purchase Orders")
    with get_session() as s:
        pos = s.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
    for po in pos:
        st.write(f"PO {po.po_number} — Supplier: {po.supplier.name if po.supplier else '—'} — Received: {po.received}")
        for item in po.items:
            st.write(f" - {item.product.name if item.product else item.product_id}: {item.quantity} @ {item.unit_cost}")
        st.markdown('---')

    st.subheader("Create PO")
    with st.form("create_po"):
        po_number = st.text_input("PO Number")
        supplier_id = st.number_input("Supplier ID", value=0)
        sku = st.text_input("Product SKU")
        qty = st.number_input("Quantity", value=1)
        unit_cost = st.number_input("Unit cost", value=0.0, format="%.2f")
        submitted = st.form_submit_button("Create PO")
        if submitted:
            with get_session() as s:
                po = PurchaseOrder(po_number=po_number, supplier_id=int(supplier_id) if supplier_id else None)
                s.add(po)
                s.flush()
                # Attach item
                p = s.query(Product).filter(Product.sku == sku).first()
                if not p:
                    st.error("Product SKU not found")
                else:
                    item = POItem(po_id=po.id, product_id=p.id, quantity=int(qty), unit_cost=float(unit_cost))
                    po.items.append(item)
                    s.commit()
                    st.success("PO created")

    st.subheader("Receive PO")
    with st.form("receive"):
        po_num = st.text_input("PO Number to receive")
        submitted = st.form_submit_button("Receive")
        if submitted:
            with get_session() as s:
                po = s.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_num).first()
                if not po:
                    st.error("PO not found")
                else:
                    po.received = True
                    for item in po.items:
                        # update inventory
                        prod = s.query(Product).get(item.product_id)
                        if not prod:
                            continue
                        if not prod.inventory:
                            inv = Inventory(product_id=prod.id, qty_on_hand=item.quantity, reorder_point=10)
                            s.add(inv)
                        else:
                            prod.inventory.qty_on_hand += item.quantity
                            prod.inventory.last_updated = datetime.utcnow()
                    s.commit()
                    st.success("PO received and inventory updated")
