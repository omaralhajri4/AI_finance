import streamlit as st
import pandas as pd
from openai import OpenAI

# =========================
# OpenAI API Key from Streamlit Secrets
# =========================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =========================
# Page Settings
# =========================
st.set_page_config(
    page_title="مِعيار",
    page_icon="📊",
    layout="wide"
)

# =========================
# App Title
# =========================
st.title("📊 مِعيار")
st.write("منصة ذكية تساعد أصحاب المشاريع الصغيرة على تحليل المبيعات والمصاريف واتخاذ قرارات أفضل.")

st.markdown("---")

# =========================
# Instructions
# =========================
st.subheader("📁 ارفع ملف المبيعات")

st.write("""
يجب أن يحتوي ملف Excel على الأعمدة التالية:

- Date
- Product
- Quantity
- Selling Price
- Cost Price
- Other Expenses
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

# =========================
# Main App Logic
# =========================
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        st.subheader("👀 معاينة البيانات")
        st.dataframe(df, use_container_width=True)

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"الملف ناقص الأعمدة التالية: {missing_columns}")
            st.stop()

        # Convert numeric columns
        numeric_columns = ["Quantity", "Selling Price", "Cost Price", "Other Expenses"]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=numeric_columns)

        if df.empty:
            st.error("لا توجد بيانات صالحة للتحليل بعد تنظيف الملف.")
            st.stop()

        # Calculations
        df["Revenue"] = df["Quantity"] * df["Selling Price"]
        df["Total Cost"] = df["Quantity"] * df["Cost Price"]
        df["Profit"] = df["Revenue"] - df["Total Cost"] - df["Other Expenses"]

        total_revenue = df["Revenue"].sum()
        total_cost = df["Total Cost"].sum()
        total_expenses = df["Other Expenses"].sum()
        net_profit = df["Profit"].sum()

        product_summary = df.groupby("Product").agg({
            "Quantity": "sum",
            "Revenue": "sum",
            "Total Cost": "sum",
            "Other Expenses": "sum",
            "Profit": "sum"
        }).reset_index()

        best_selling_product = product_summary.sort_values("Quantity", ascending=False).iloc[0]
        most_profitable_product = product_summary.sort_values("Profit", ascending=False).iloc[0]
        weakest_product = product_summary.sort_values("Profit", ascending=True).iloc[0]

        st.markdown("---")

        # =========================
        # Dashboard
        # =========================
        st.subheader("📌 ملخص الأداء المالي")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("إجمالي المبيعات", f"{total_revenue:.3f} OMR")
        col2.metric("تكلفة المنتجات", f"{total_cost:.3f} OMR")
        col3.metric("المصاريف الأخرى", f"{total_expenses:.3f} OMR")
        col4.metric("صافي الربح", f"{net_profit:.3f} OMR")

        st.markdown("---")

        # =========================
        # Product Analysis
        # =========================
        st.subheader("📦 تحليل المنتجات")
        st.dataframe(product_summary, use_container_width=True)

        st.write(f"🏆 أكثر منتج مبيعًا: *{best_selling_product['Product']}*")
        st.write(f"💰 أكثر منتج ربحية: *{most_profitable_product['Product']}*")
        st.write(f"⚠️ أضعف منتج من ناحية الربح: *{weakest_product['Product']}*")

        st.markdown("---")

        # =========================
        # Charts
        # =========================
        st.subheader("📈 الرسوم البيانية")

        chart_data = product_summary.set_index("Product")[["Revenue", "Profit"]]
        st.bar_chart(chart_data)

        st.markdown("---")

        # =========================
        # AI Report
        # =========================
        st.subheader("🤖 تقرير الذكاء الاصطناعي")

        if st.button("حلّل مشروعي"):
            with st.spinner("جاري تحليل بيانات المشروع..."):

                business_data = f"""
                إجمالي المبيعات: {total_revenue:.3f} ريال عماني
                إجمالي تكلفة المنتجات: {total_cost:.3f} ريال عماني
                المصاريف الأخرى: {total_expenses:.3f} ريال عماني
                صافي الربح: {net_profit:.3f} ريال عماني

                أكثر منتج مبيعًا:
                {best_selling_product["Product"]} بعدد {best_selling_product["Quantity"]} وحدة

                أكثر منتج ربحية:
                {most_profitable_product["Product"]} بربح {most_profitable_product["Profit"]:.3f} ريال عماني

                أضعف منتج من ناحية الربح:
                {weakest_product["Product"]} بربح {weakest_product["Profit"]:.3f} ريال عماني

                ملخص المنتجات:
                {product_summary.to_string(index=False)}
                """

                prompt = f"""
                أنت مستشار أعمال ذكي متخصص في مساعدة المؤسسات الصغيرة والمتوسطة في سلطنة عمان.

                حلل بيانات المشروع التالية واكتب تقريرًا واضحًا باللغة العربية.

                المطلوب في التقرير:
                1. ملخص بسيط للأداء المالي.
                2. نقاط القوة في المشروع.
                3. نقاط الضعف أو المخاطر.
                4. توصيات عملية لزيادة الربح.
                5. اقتراح لتحسين التسعير أو تقليل التكاليف.
                6. اقتراح تسويقي بسيط يناسب السوق العماني.
                7. اختم بخلاصة قصيرة لصاحب المشروع.

                اجعل الأسلوب بسيطًا ومباشرًا ومناسبًا لصاحب مشروع صغير، وليس بلغة معقدة.

                بيانات المشروع:
                {business_data}
                """

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=prompt
                )

                ai_report = response.output_text

                st.success("تم إنشاء التقرير بنجاح")
                st.write(ai_report)

                st.download_button(
                    label="تحميل التقرير",
                    data=ai_report,
                    file_name="ai_business_report.txt",
                    mime="text/plain"
                )

    except Exception as e:
        st.error("حدث خطأ أثناء قراءة أو تحليل الملف.")
        st.write(e)

else:
    st.info("ارفع ملف Excel للبدء في التحليل.")
