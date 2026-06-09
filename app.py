import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO
from openai import OpenAI
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


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
# Simple Login Users
# =========================
USERS = {
    "omar": "1234",
    "admin": "admin123"
}


# =========================
# Save Reports File
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
# CSS
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
# Helpers
# =========================
def normalize_columns(df):
    column_mapping = {
        "التاريخ": "Date",
        "تاريخ": "Date",
        "اليوم": "Date",

        "المنتج": "Product",
        "اسم المنتج": "Product",
        "الصنف": "Product",

        "الكمية": "Quantity",
        "عدد": "Quantity",

        "سعر البيع": "Selling Price",
        "السعر": "Selling Price",

        "تكلفة المنتج": "Cost Price",
        "سعر التكلفة": "Cost Price",
        "التكلفة": "Cost Price",

        "المصاريف": "Other Expenses",
        "مصاريف أخرى": "Other Expenses",
        "المصاريف الأخرى": "Other Expenses"
    }

    return df.rename(columns=column_mapping)


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


def create_pdf(report_text):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle("Mi3yar Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "Mi3yar Business Report")

    pdf.setFont("Helvetica", 10)

    y = height - 90

    # ملاحظة: PDF هنا يدعم النص الإنجليزي بشكل أفضل.
    # التقرير العربي محفوظ بشكل ممتاز في TXT داخل التطبيق.
    clean_text = report_text.replace("#", "").replace("*", "")

    lines = clean_text.split("\n")

    for line in lines:
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50

        safe_line = line.encode("latin-1", "ignore").decode("latin-1")
        pdf.drawString(50, y, safe_line[:100])
        y -= 15

    pdf.save()
    buffer.seek(0)
    return buffer


# =========================
# Login
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


if not st.session_state.logged_in:
    st.markdown('<div class="big-title">معيار</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">منصة تحليل ذكية للمشاريع الصغيرة</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.subheader("تسجيل الدخول")

    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

    st.info("للتجربة: username = omar ، password = 1234")
    st.stop()


# =========================
# Sidebar
# =========================
st.sidebar.title("📊 معيار")
st.sidebar.write(f"مرحبًا، {st.session_state.username}")

page = st.sidebar.radio(
    "القائمة",
    ["الرئيسية", "تحليل البيانات", "التقارير المحفوظة", "عن معيار"]
)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


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
        st.subheader("📈 رسوم وتحليل")
        st.write("يوضح أداء المنتجات والأيام الأفضل للمبيعات.")

    with col3:
        st.subheader("🧾 تقارير ذكية")
        st.write("ينشئ تقريرًا عمليًا يساعدك في التسعير والمخزون والتسويق.")

    st.markdown("---")
    st.success("ابدأ من صفحة تحليل البيانات.")


# =========================
# Analysis Page
# =========================
elif page == "تحليل البيانات":

    st.title("📊 تحليل بيانات المشروع")

    st.write("ارفع ملف Excel يحتوي على بيانات المبيعات والمصاريف، وسيقوم معيار بتحليل الأداء.")

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
الملف يجب أن يحتوي على الأعمدة التالية بالإنجليزي:

Date, Product, Quantity, Selling Price, Cost Price, Other Expenses

أو بالعربي:

التاريخ, المنتج, الكمية, سعر البيع, تكلفة المنتج, المصاريف
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
            df = pd.read_excel(uploaded_file)
            df = normalize_columns(df)

            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.error(f"الملف ناقص الأعمدة التالية: {missing_columns}")
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
                st.error("لا توجد بيانات صالحة للتحليل.")
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

            st.subheader("👀 معاينة البيانات")
            st.dataframe(df, use_container_width=True)

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
                    "username": st.session_state.username,
                    "business_name": business_name,
                    "business_type": business_type,
                    "governorate": governorate,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_revenue": round(total_revenue, 3),
                    "net_profit": round(net_profit, 3),
                    "profit_margin": round(profit_margin, 2),
                    "report": ai_report
                }

                save_report(report_data)

                st.download_button(
                    label="تحميل التقرير TXT",
                    data=ai_report,
                    file_name="mi3yar_report.txt",
                    mime="text/plain"
                )

                pdf_file = create_pdf(ai_report)

                st.download_button(
                    label="تحميل التقرير PDF",
                    data=pdf_file,
                    file_name="mi3yar_report.pdf",
                    mime="application/pdf"
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
        if report.get("username") == st.session_state.username
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
- دعم ملفات Excel بالعربية والإنجليزية.
- تحليل المبيعات والتكاليف والأرباح.
- حساب هامش الربح.
- تحليل حسب المنتجات.
- تحليل حسب الأيام.
- رسوم بيانية واضحة.
- تقرير ذكي قابل للتحميل.
- حفظ التقارير السابقة.
- تسجيل دخول بسيط للنسخة التجريبية.
""")
