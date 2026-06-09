import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from openai import OpenAI
import plotly.express as px
from supabase import create_client


# =========================
# Page Settings
# =========================
st.set_page_config(
    page_title="معيار",
    page_icon="📊",
    layout="wide"
)


# =========================
# OpenAI Client
# =========================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None


# =========================
# Supabase Client
# =========================
try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception:
    supabase = None


# =========================
# Saved Reports Local File
# ملاحظة: هذا حفظ مؤقت داخل Streamlit.
# لاحقًا الأفضل نحفظ التقارير داخل Supabase Database.
# =========================
REPORTS_FILE = "saved_reports.json"


def load_saved_reports():
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_report(report_data):
    reports = load_saved_reports()
    reports.append(report_data)

    with open(REPORTS_FILE, "w", encoding="utf-8") as file:
        json.dump(reports, file, ensure_ascii=False, indent=4)


# =========================
# Styling
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.big-title {
    font-size: 44px;
    font-weight: 800;
    color: #1f2937;
}
.subtitle {
    font-size: 20px;
    color: #4b5563;
}
.small-note {
    color: #6b7280;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# Supabase Auth Functions
# =========================
def login_user(email, password):
    if supabase is None:
        return False, "Supabase غير متصل. تأكد من إضافة SUPABASE_URL و SUPABASE_KEY في Streamlit Secrets."

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user is not None:
            st.session_state.logged_in = True
            st.session_state.user_email = response.user.email
            st.session_state.user_id = response.user.id

            if response.session is not None:
                st.session_state.access_token = response.session.access_token

            return True, "تم تسجيل الدخول بنجاح"

        return False, "بيانات الدخول غير صحيحة"

    except Exception as e:
        return False, f"تعذر تسجيل الدخول: {e}"


def signup_user(email, password):
    if supabase is None:
        return False, "Supabase غير متصل. تأكد من إضافة SUPABASE_URL و SUPABASE_KEY في Streamlit Secrets."

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user is not None:
            return True, "تم إنشاء الحساب. إذا كان تأكيد الإيميل مفعلًا في Supabase، افتح بريدك واضغط رابط التأكيد قبل تسجيل الدخول."

        return False, "لم يتم إنشاء الحساب."

    except Exception as e:
        return False, f"تعذر إنشاء الحساب: {e}"


def logout_user():
    try:
        if supabase is not None:
            supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_id = ""
    st.session_state.access_token = ""
    st.rerun()


# =========================
# Basic Column Mapping
# =========================
def normalize_columns_basic(df):
    column_mapping = {
        "التاريخ": "Date",
        "تاريخ": "Date",
        "تاريخ البيع": "Date",
        "تاريخ الفاتورة": "Date",
        "اليوم": "Date",

        "المنتج": "Product",
        "اسم المنتج": "Product",
        "الصنف": "Product",
        "اسم الصنف": "Product",
        "الوصف": "Product",
        "البيان": "Product",

        "الكمية": "Quantity",
        "عدد": "Quantity",
        "العدد": "Quantity",
        "العدد المباع": "Quantity",
        "الكمية المباعة": "Quantity",

        "سعر البيع": "Selling Price",
        "السعر": "Selling Price",
        "سعر الوحدة": "Selling Price",
        "قيمة البيع": "Selling Price",

        "تكلفة المنتج": "Cost Price",
        "سعر التكلفة": "Cost Price",
        "التكلفة": "Cost Price",
        "تكلفة الشراء": "Cost Price",

        "المصاريف": "Other Expenses",
        "مصاريف أخرى": "Other Expenses",
        "المصاريف الأخرى": "Other Expenses",
        "تكاليف إضافية": "Other Expenses",

        "Item": "Product",
        "Item Name": "Product",
        "Product": "Product",
        "Product Name": "Product",
        "Description": "Product",

        "Qty": "Quantity",
        "Quantity": "Quantity",
        "Sold Qty": "Quantity",
        "Units Sold": "Quantity",

        "Price": "Selling Price",
        "Unit Price": "Selling Price",
        "Sales Price": "Selling Price",
        "Selling Price": "Selling Price",

        "Cost": "Cost Price",
        "Unit Cost": "Cost Price",
        "Purchase Cost": "Cost Price",
        "Cost Price": "Cost Price",

        "Expenses": "Other Expenses",
        "Extra Cost": "Other Expenses",
        "Other Cost": "Other Expenses",
        "Other Expenses": "Other Expenses",

        "Date": "Date",
        "Sale Date": "Date",
        "Invoice Date": "Date"
    }

    return df.rename(columns=column_mapping)


# =========================
# AI Column Detection
# =========================
def detect_columns_with_ai(df):
    """
    AI يفهم عناوين الجدول ويرجع mapping.
    الحسابات نفسها تتم لاحقًا بـ Python.
    """

    if client is None:
        return {}

    sample_df = df.head(5).copy()
    columns = list(df.columns)
    sample_rows = sample_df.to_dict(orient="records")

    prompt = f"""
أنت مساعد متخصص في فهم جداول المبيعات للمؤسسات الصغيرة.

لدي جدول مرفوع من صاحب مشروع. أريدك أن تحدد أي عمود يمثل كل خانة من الخانات القياسية المطلوبة.

الخانات القياسية المطلوبة:
- Date
- Product
- Quantity
- Selling Price
- Cost Price
- Other Expenses

أسماء الأعمدة الموجودة في الملف:
{columns}

أول 5 صفوف من الجدول:
{sample_rows}

المطلوب:
أرجع JSON فقط بدون أي شرح.

صيغة الرد:
{{
  "Date": "اسم العمود المناسب أو null",
  "Product": "اسم العمود المناسب أو null",
  "Quantity": "اسم العمود المناسب أو null",
  "Selling Price": "اسم العمود المناسب أو null",
  "Cost Price": "اسم العمود المناسب أو null",
  "Other Expenses": "اسم العمود المناسب أو null"
}}

قواعد مهمة:
- إذا لم تجد عمودًا مناسبًا، ضع null.
- لا تختر عمودًا إلا إذا كان واضحًا من الاسم أو البيانات.
- لا تكتب أي نص خارج JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد يفهم جداول المبيعات ويرجع JSON فقط."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        content = content.replace("json", "").replace("", "").strip()

        mapping = json.loads(content)

        clean_mapping = {}

        for standard_col, original_col in mapping.items():
            if original_col is not None and original_col in df.columns:
                clean_mapping[original_col] = standard_col

        return clean_mapping

    except Exception:
        return {}


def normalize_columns_with_ai(df):
    required_columns = [
        "Date",
        "Product",
        "Quantity",
        "Selling Price",
        "Cost Price",
        "Other Expenses"
    ]

    df_basic = normalize_columns_basic(df.copy())

    missing_after_basic = [
        col for col in required_columns
        if col not in df_basic.columns
    ]

    if not missing_after_basic:
        return df_basic, "تم التعرف على الأعمدة تلقائيًا باستخدام القواعد الأساسية."

    ai_mapping = detect_columns_with_ai(df)

    if ai_mapping:
        df_ai = df.rename(columns=ai_mapping)
        df_ai = normalize_columns_basic(df_ai)
        return df_ai, "تم التعرف على بعض أو كل الأعمدة باستخدام الذكاء الاصطناعي."

    return df_basic, "لم يتمكن النظام من التعرف على كل الأعمدة. قد تحتاج لتعديل أسماء الأعمدة."


# =========================
# Fallback Report
# =========================
def generate_fallback_report(
    business_name,
    business_type,
    governorate,
    total_revenue,
    total_cost,
    total_expenses,
    net_profit,
    profit_margin,
    best_selling_product,
    most_profitable_product,
    weakest_product,
    best_day
):
    return f"""
# تقرير معيار

## بيانات المشروع
اسم المشروع: {business_name}  
نوع النشاط: {business_type}  
المحافظة: {governorate}  
تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}

## ملخص الأداء المالي
حقق المشروع إجمالي مبيعات بقيمة *{total_revenue:.3f} ريال عماني*.

بلغت تكلفة المنتجات *{total_cost:.3f} ريال عماني، وبلغت المصاريف الأخرى *{total_expenses:.3f} ريال عماني**.

صافي الربح هو *{net_profit:.3f} ريال عماني*.

هامش الربح التقريبي هو *{profit_margin:.2f}%*.

## تحليل المنتجات
أكثر منتج مبيعًا هو *{best_selling_product["Product"]}* بعدد *{best_selling_product["Quantity"]}* وحدة.

أكثر منتج ربحية هو *{most_profitable_product["Product"]}* بربح *{most_profitable_product["Profit"]:.3f} ريال عماني*.

أضعف منتج من ناحية الربح هو *{weakest_product["Product"]}* بربح *{weakest_product["Profit"]:.3f} ريال عماني*.

## تحليل الأيام
أفضل يوم من ناحية المبيعات هو *{best_day["Date"]}* بمبيعات *{best_day["Revenue"]:.3f} ريال عماني*.

## التوصيات
- ركّز على المنتج الأعلى ربحية وزد توفره في المخزون.
- راجع سعر أو تكلفة المنتج الأضعف ربحية.
- إذا كان منتج يبيع كثيرًا لكن ربحه ضعيف، ارفع سعره قليلًا أو خفّض تكلفته.
- قلّل المصاريف غير الضرورية إذا كانت تأخذ نسبة كبيرة من المبيعات.
- استخدم عروض نهاية الأسبوع لتحريك المنتجات الضعيفة.
- تابع المبيعات أسبوعيًا بدل الانتظار لنهاية الشهر.

## الخلاصة
معيار يساعد صاحب المشروع على تحويل الأرقام اليومية إلى قرارات واضحة في التسعير، المخزون، التسويق، وتقليل التكاليف.
"""


# =========================
# Session State
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if "access_token" not in st.session_state:
    st.session_state.access_token = ""


# =========================
# Login / Signup Page
# =========================
if not st.session_state.logged_in:
    st.markdown('<div class="big-title">معيار</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">منصة تحليل ذكية للمشاريع الصغيرة</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب"])

    with tab1:
        st.subheader("تسجيل الدخول")

        email = st.text_input("البريد الإلكتروني", key="login_email")
        password = st.text_input("كلمة المرور", type="password", key="login_password")

        if st.button("دخول"):
            if not email or not password:
                st.error("اكتب البريد الإلكتروني وكلمة المرور.")
            else:
                success, message = login_user(email, password)

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.subheader("إنشاء حساب جديد")

        new_email = st.text_input("البريد الإلكتروني", key="signup_email")
        new_password = st.text_input("كلمة المرور", type="password", key="signup_password")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="confirm_password")

        if st.button("إنشاء الحساب"):
            if not new_email or not new_password:
                st.error("اكتب البريد الإلكتروني وكلمة المرور.")
            elif new_password != confirm_password:
                st.error("كلمتا المرور غير متطابقتين.")
            elif len(new_password) < 6:
                st.error("كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
            else:
                success, message = signup_user(new_email, new_password)

                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.stop()


# =========================
# Sidebar
# =========================
st.sidebar.title("📊 معيار")
st.sidebar.write(f"مرحبًا، {st.session_state.user_email}")

page = st.sidebar.radio(
    "القائمة",
    ["الرئيسية", "تحليل البيانات", "التقارير المحفوظة", "عن معيار"]
)

if st.sidebar.button("تسجيل الخروج"):
    logout_user()


# =========================
# Home Page
# =========================
if page == "الرئيسية":
    st.markdown('<div class="big-title">معيار</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">منصة تحول بيانات المبيعات والمصاريف إلى قرارات عملية لأصحاب المشاريع الصغيرة.</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 تحليل مالي")
        st.write("يعرض المبيعات، التكاليف، الأرباح، وهامش الربح.")

    with col2:
        st.subheader("🧠 فهم ذكي للجداول")
        st.write("يتعرف على خانات الجدول حتى لو كانت بأسماء مختلفة.")

    with col3:
        st.subheader("🧾 تقارير عملية")
        st.write("ينشئ تقريرًا يساعدك في التسعير، المخزون، والتسويق.")

    st.markdown("---")
    st.success("ابدأ من صفحة تحليل البيانات.")


# =========================
# Analysis Page
# =========================
elif page == "تحليل البيانات":

    st.title("📊 تحليل بيانات المشروع")

    st.write("ارفع ملف Excel يحتوي على بيانات المبيعات، وسيحاول معيار فهم الخانات وتحليل الأداء.")

    st.markdown("---")

    st.subheader("🏪 بيانات المشروع")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        business_name = st.text_input("اسم المشروع", value="مشروعي")

    with col_b:
        business_type = st.selectbox(
            "نوع النشاط",
            ["مقهى", "مطعم", "عطور", "ملابس", "صالون", "متجر إلكتروني", "خدمات", "أخرى"]
        )

    with col_c:
        governorate = st.selectbox(
            "المحافظة",
            [
                "مسقط",
                "شمال الشرقية",
                "جنوب الشرقية",
                "الداخلية",
                "ظفار",
                "شمال الباطنة",
                "جنوب الباطنة",
                "الظاهرة",
                "البريمي",
                "مسندم",
                "الوسطى"
            ]
        )

    st.markdown("---")

    st.subheader("📁 ارفع ملف المبيعات")

    st.write("""
يفضل أن يحتوي الملف على خانات مثل:

- التاريخ / Date
- المنتج / Product
- الكمية / Quantity
- سعر البيع / Selling Price
- تكلفة المنتج / Cost Price
- المصاريف / Other Expenses

إذا كانت أسماء الأعمدة مختلفة، سيحاول معيار فهمها تلقائيًا.
""")

    uploaded_file = st.file_uploader(
        "ارفع ملف Excel بصيغة xlsx",
        type=["xlsx"]
    )

    required_columns = [
        "Date",
        "Product",
        "Quantity",
        "Selling Price",
        "Cost Price",
        "Other Expenses"
    ]

    if uploaded_file is not None:
        try:
            original_df = pd.read_excel(uploaded_file)

            st.subheader("📄 الجدول الأصلي")
            st.dataframe(original_df, use_container_width=True)

            df, detection_message = normalize_columns_with_ai(original_df)

            st.info(detection_message)

            st.subheader("✅ الجدول بعد فهم الخانات")
            st.dataframe(df, use_container_width=True)

            missing_columns = [
                col for col in required_columns
                if col not in df.columns
            ]

            if missing_columns:
                st.error(f"ما زالت هذه الخانات ناقصة: {missing_columns}")
                st.warning("عدّل أسماء الأعمدة في الملف أو أضف الخانات الناقصة ثم ارفع الملف مرة ثانية.")
                st.stop()

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            numeric_columns = [
                "Quantity",
                "Selling Price",
                "Cost Price",
                "Other Expenses"
            ]

            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["Date"] + numeric_columns)

            if df.empty:
                st.error("لا توجد بيانات صالحة للتحليل بعد تنظيف الملف.")
                st.stop()

            df["Revenue"] = df["Quantity"] * df["Selling Price"]
            df["Total Cost"] = df["Quantity"] * df["Cost Price"]
            df["Profit"] = df["Revenue"] - df["Total Cost"] - df["Other Expenses"]

            total_revenue = df["Revenue"].sum()
            total_cost = df["Total Cost"].sum()
            total_expenses = df["Other Expenses"].sum()
            net_profit = df["Profit"].sum()

            profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

            product_summary = df.groupby("Product").agg({
                "Quantity": "sum",
                "Revenue": "sum",
                "Total Cost": "sum",
                "Other Expenses": "sum",
                "Profit": "sum"
            }).reset_index()

            product_summary["Profit Margin %"] = (
                product_summary["Profit"] / product_summary["Revenue"] * 100
            ).fillna(0)

            daily_summary = df.groupby(df["Date"].dt.date).agg({
                "Revenue": "sum",
                "Profit": "sum",
                "Quantity": "sum"
            }).reset_index()

            best_selling_product = product_summary.sort_values("Quantity", ascending=False).iloc[0]
            most_profitable_product = product_summary.sort_values("Profit", ascending=False).iloc[0]
            weakest_product = product_summary.sort_values("Profit", ascending=True).iloc[0]
            best_day = daily_summary.sort_values("Revenue", ascending=False).iloc[0]

            st.markdown("---")

            st.subheader("📌 لوحة الأداء المالي")

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric("إجمالي المبيعات", f"{total_revenue:.3f} OMR")
            col2.metric("تكلفة المنتجات", f"{total_cost:.3f} OMR")
            col3.metric("المصاريف الأخرى", f"{total_expenses:.3f} OMR")
            col4.metric("صافي الربح", f"{net_profit:.3f} OMR")
            col5.metric("هامش الربح", f"{profit_margin:.2f}%")

            st.markdown("---")

            st.subheader("📦 تحليل المنتجات")

            st.dataframe(product_summary, use_container_width=True)

            col6, col7, col8 = st.columns(3)

            with col6:
                st.success(f"🏆 الأكثر مبيعًا: {best_selling_product['Product']}")

            with col7:
                st.success(f"💰 الأعلى ربحية: {most_profitable_product['Product']}")

            with col8:
                st.warning(f"⚠️ الأضعف ربحية: {weakest_product['Product']}")

            st.markdown("---")

            st.subheader("📅 تحليل حسب الأيام")

            st.dataframe(daily_summary, use_container_width=True)

            st.info(f"أفضل يوم من ناحية المبيعات: {best_day['Date']} بمبيعات {best_day['Revenue']:.3f} OMR")

            st.markdown("---")

            st.subheader("📈 الرسوم البيانية")

            fig1 = px.bar(
                product_summary,
                x="Product",
                y="Revenue",
                title="المبيعات حسب المنتج",
                text_auto=True
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.bar(
                product_summary,
                x="Product",
                y="Profit",
                title="الربح حسب المنتج",
                text_auto=True
            )
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = px.line(
                daily_summary,
                x="Date",
                y="Revenue",
                title="المبيعات حسب الأيام",
                markers=True
            )
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("---")

            st.subheader("🧾 تقرير معيار")

            if st.button("حلّل مشروعي"):

                business_data = f"""
اسم المشروع: {business_name}
نوع النشاط: {business_type}
المحافظة: {governorate}

إجمالي المبيعات: {total_revenue:.3f} ريال عماني
إجمالي تكلفة المنتجات: {total_cost:.3f} ريال عماني
المصاريف الأخرى: {total_expenses:.3f} ريال عماني
صافي الربح: {net_profit:.3f} ريال عماني
هامش الربح: {profit_margin:.2f}%

أكثر منتج مبيعًا:
{best_selling_product["Product"]} بعدد {best_selling_product["Quantity"]} وحدة

أكثر منتج ربحية:
{most_profitable_product["Product"]} بربح {most_profitable_product["Profit"]:.3f} ريال عماني

أضعف منتج من ناحية الربح:
{weakest_product["Product"]} بربح {weakest_product["Profit"]:.3f} ريال عماني

أفضل يوم مبيعات:
{best_day["Date"]} بمبيعات {best_day["Revenue"]:.3f} ريال عماني

ملخص المنتجات:
{product_summary.to_string(index=False)}

ملخص الأيام:
{daily_summary.to_string(index=False)}
"""

                prompt = f"""
أنت مستشار أعمال في منصة معيار، وهي منصة عمانية تساعد المؤسسات الصغيرة على فهم بيانات المبيعات والمصاريف واتخاذ قرارات أفضل.

حلل بيانات المشروع التالية واكتب تقريرًا واضحًا باللغة العربية.

المطلوب:
1. ملخص الأداء المالي.
2. نقاط القوة.
3. نقاط الضعف أو المخاطر.
4. توصيات عملية لزيادة الربح.
5. اقتراح لتحسين التسعير أو تقليل التكاليف.
6. اقتراح تسويقي يناسب نوع النشاط والمحافظة في سلطنة عمان.
7. خلاصة قصيرة لصاحب المشروع.

اكتب بأسلوب واضح ومباشر.
لا تقل إنك نموذج ذكاء اصطناعي.
اكتب التقرير كأنه صادر من منصة معيار.

بيانات المشروع:
{business_data}
"""

                with st.spinner("جاري إنشاء التقرير..."):
                    try:
                        if client is None:
                            raise Exception("OpenAI client not available")

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "أنت مستشار أعمال لمنصة معيار."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )

                        ai_report = response.choices[0].message.content

                    except Exception:
                        ai_report = generate_fallback_report(
                            business_name,
                            business_type,
                            governorate,
                            total_revenue,
                            total_cost,
                            total_expenses,
                            net_profit,
                            profit_margin,
                            best_selling_product,
                            most_profitable_product,
                            weakest_product,
                            best_day
                        )

                st.success("تم إنشاء التقرير بنجاح")
                st.markdown(ai_report)

                report_data = {
                    "user_id": st.session_state.user_id,
                    "user_email": st.session_state.user_email,
                    "business_name": business_name,
                    "business_type": business_type,
                    "governorate": governorate,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_revenue": round(float(total_revenue), 3),
                    "net_profit": round(float(net_profit), 3),
                    "profit_margin": round(float(profit_margin), 2),
                    "report": ai_report
                }

                save_report(report_data)

                st.download_button(
                    label="تحميل التقرير TXT",
                    data=ai_report,
                    file_name="mi3yar_report.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error("حدث خطأ أثناء قراءة أو تحليل الملف.")
            st.write(e)

    else:
        st.info("ارفع ملف Excel للبدء في التحليل.")


# =========================
# Saved Reports Page
# =========================
elif page == "التقارير المحفوظة":

    st.title("📚 التقارير المحفوظة")

    reports = load_saved_reports()

    user_reports = [
        report for report in reports
        if report.get("user_id") == st.session_state.user_id
    ]

    if not user_reports:
        st.info("لا توجد تقارير محفوظة حتى الآن.")
    else:
        for i, report in enumerate(reversed(user_reports), start=1):
            with st.expander(f"{i}. {report['business_name']} - {report['date']}"):
                st.write(f"نوع النشاط: {report['business_type']}")
                st.write(f"المحافظة: {report['governorate']}")
                st.write(f"إجمالي المبيعات: {report['total_revenue']} OMR")
                st.write(f"صافي الربح: {report['net_profit']} OMR")
                st.write(f"هامش الربح: {report['profit_margin']}%")
                st.markdown(report["report"])


# =========================
# About Page
# =========================
elif page == "عن معيار":

    st.title("عن معيار")

    st.write("""
*معيار* منصة تحليل ذكية موجهة لأصحاب المشاريع الصغيرة والمتوسطة في سلطنة عمان.

تساعد المنصة صاحب المشروع على فهم مبيعاته ومصاريفه وأرباحه بطريقة سهلة، وتحويل البيانات اليومية إلى توصيات عملية في التسعير، المخزون، التسويق، وتقليل التكاليف.
""")

    st.markdown("---")

    st.subheader("مميزات معيار")

    st.write("""
- تسجيل دخول حقيقي بالإيميل وكلمة المرور.
- دعم ملفات Excel بالعربية والإنجليزية.
- فهم ذكي لأسماء الأعمدة حتى لو كانت مختلفة.
- تحليل المبيعات والتكاليف والأرباح.
- حساب هامش الربح.
- تحليل حسب المنتجات.
- تحليل حسب الأيام.
- رسوم بيانية واضحة.
- تقرير ذكي قابل للتحميل.
- حفظ التقارير حسب المستخدم.
""")
