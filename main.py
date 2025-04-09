import os
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import plotly.graph_objs as go

app = Flask(__name__)

file_path = os.path.join(os.path.dirname(__file__), 'dff.csv')
df = pd.read_csv(file_path)

# Template HTML trực tiếp trong mã
html_template = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nhập Mã Cổ Phiếu</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 20px;
        }

        .container {
            width: 90%;
            margin: 0 auto;
            text-align: center;
        }

        h1 {
            color: #003366;
        }

        form {
            margin-bottom: 20px;
        }

        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            width: 200px;
            margin-right: 10px;
        }

        button {
            padding: 10px 20px;
            background-color: #FF7F00;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background-color: #e67400;
        }

        .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 30px;
        }

        .grid-item {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .error {
            color: red;
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            text-align: center;
            }

        table, th, td {
            border: 1px solid #ddd;
        }

        th, td {
            padding: 12px;
            text-align: center;
        }

        th {
            background-color: #f2f2f2;
            color: #333;
        }

        td {
            background-color: #fff;
        }

        tr:hover {
            background-color: #f5f5f5;
        }

        .table-striped {
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .table-striped th, .table-striped td {
            padding: 10px 15px;
            font-size: 16px;
            border: 1px solid #ddd;
        }

        .table-striped th {
            background-color: #144e8c;
            color: white;
        }

        .table-striped td {
            background-color: #f9f9f9;
        }

        .table-striped tr:hover {
            background-color: #e6f7ff;
        }

        .grid-item {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            height: 520px;
            overflow-y: auto;
        }

    </style>
</head>
<body>

    <div class="container">
        <h1>Nhập Mã Cổ Phiếu</h1>
        <form method="POST">
            <label for="stock_code">Mã Cổ Phiếu:</label>
            <input type="text" id="stock_code" name="stock_code" placeholder="Nhập mã cổ phiếu" required>
            <button type="submit">Xem</button>
        </form>

        {% if result %}
        <p class="error">{{ result }}</p>
        {% endif %}

        {% if stock_code and not result %}
            <h2>Thông tin cổ phiếu: {{ stock_code }}</h2>
            <div class="grid-container">
                <div class="grid-item">
                    <h3>Biến động cụm của {{ stock_code }} qua từng năm</h3>
                    {{ cluster_table | safe }}
                </div>

                <div class="grid-item">
                    {{ cluster_cards | safe }}
                </div>

                <div class="grid-item">
                    <h3>Chỉ số Thanh khoản hiện hành của {{ stock_code }}</h3>
                    {{ liquidity_plot | safe }}
                </div>
                <div class="grid-item">
                    <h3>Chỉ số Đòn bẩy của {{ stock_code }}</h3>
                    {{ leverage_plot | safe }}
                </div>
                <div class="grid-item">
                    <h3>Chỉ số Hiệu quả hoạt động của {{ stock_code }}</h3>
                    {{ efficiency_plot | safe }}
                </div>
                <div class="grid-item">
                    <h3>Chỉ số EPS của {{ stock_code }}</h3>
                    {{ eps_plot | safe }}
                </div>           
                <div class="grid-item">
                    <h3>Chỉ số BVPS của {{ stock_code }}</h3>
                    {{ bvps_plot | safe }}
                </div>       
                <div class="grid-item">
                    <h3>Chỉ số P/E của {{ stock_code }}</h3>
                    {{ pe_plot | safe }}
                </div>

            </div>
        {% endif %}
    </div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    stock_code = None
    liquidity_plot = None
    leverage_plot = None
    efficiency_plot = None
    eps_plot = None
    bvps_plot = None
    pe_plot = None
    cluster_table_html = ""
    cluster_cards_html = ""

    if request.method == "POST":
        stock_code = request.form.get("stock_code").upper()  # Chuyển mã cổ phiếu về chữ in hoa
        if stock_code in df['stock'].values:
            stock_data = df[df['stock'] == stock_code]

            # Tạo bảng Cluster
            cluster_data = stock_data[['year', 'cluster']].drop_duplicates()
            cluster_data.columns = ['Năm', 'Cụm']
            cluster_table_html = cluster_data.to_html(index=False, classes="table table-striped")

            # Tính trung bình chỉ số tài chính theo cụm
            cluster_avg = df.groupby('cluster')[['CR', 'D/E', 'D/A', 'ROA %',
                                                 'EPS', 'Inventory Turnover', 'Asset Turnover',
                                                 'P/E', 'BVPS']].mean().round(2)
            cluster_avg_dict = cluster_avg.to_dict(orient='index')

            # Thêm phần card hiển thị chỉ số của từng cụm với tab chuyển cụm
            cluster_cards_html += """
                                <div style='margin-top: 10px;'>
                                <div style='margin-bottom: 10px;'>
                                """
            cluster_cards_html += "</div>"

            # Tạo phần hiển thị thông tin chi tiết của từng cụm
            for cid, val in cluster_avg_dict.items():
                cluster_cards_html += f"""
                                <h3>Dữ liệu tài chính của Cụm {cid}</h3>
                                <div style='text-align: left; max-width: 400px; margin: 0 auto;'>
                                    <div style='background-color: #f9f9f9; border-radius: 10px; padding: 20px;'>
                                        <p><strong>Current Ratio:</strong> {val.get("CR", "-")}</p>
                                        <p><strong>Inventory Turnover:</strong> {val.get("Inventory Turnover", "-")}</p>
                                        <p><strong>Asset Turnover:</strong> {val.get("Asset Turnover", "-")}</p>
                                        <p><strong>ROA:</strong> {val.get("ROA %", "-")} %</p>
                                        <p><strong>D/E:</strong> {val.get("D/E", "-")}</p>
                                        <p><strong>D/A:</strong> {val.get("D/A", "-")}</p>
                                        <p><strong>EPS:</strong> {val.get("EPS", "-")} triệu đồng</p>
                                        <p><strong>P/E:</strong> {val.get("P/E", "-")} triệu đồng</p>
                                        <p><strong>Book Value Per Share:</strong> {val.get("BVPS", "-")} triệu đồng</p>
                                    </div>
                                </div>
                            """

            cluster_cards_html += """
                        </div>
                        <script>
                            function showCluster(id) {
                                const clusters = [""" + ",".join([f"{c}" for c in cluster_avg_dict.keys()]) + """];

                                clusters.forEach(cid => {
                                    document.getElementById('cluster_card_' + cid).style.display = 'none';
                                });

                                document.getElementById('cluster_card_' + id).style.display = 'block';
                            }
                        </script>
                        """

            # Tạo các biểu đồ Plotly
            liquidity_plot = go.Figure()
            liquidity_plot.add_trace(go.Bar(x=stock_data['year'], y=stock_data['CR'],
                                             name='CR', marker=dict(color='#154e8c')))
            liquidity_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['CR'],
                                                mode='lines+markers', name='CR', showlegend=False,
                                                line=dict(shape='spline', smoothing=1, width=3, color='#f05a22')))
            liquidity_plot.update_layout(xaxis_title="Năm",
                                          plot_bgcolor='white',
                                          paper_bgcolor='white',
                                          xaxis=dict(showgrid=False),
                                          yaxis=dict(showgrid=True, gridcolor='lightgray'))

            leverage_plot = go.Figure()
            leverage_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['D/E'],
                                               mode='lines+markers', name='D/E',
                                               line=dict(shape='spline', smoothing=1, width=3, color='#ec5924')))
            leverage_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['D/A'],
                                               mode='lines+markers', name='D/A',
                                               line=dict(shape='spline', smoothing=1, width=3, color='#154e8c')))
            leverage_plot.update_layout(xaxis_title="Năm",
                                        plot_bgcolor='white',
                                        paper_bgcolor='white',
                                        xaxis=dict(showgrid=False),
                                        yaxis=dict(showgrid=True, gridcolor='lightgray'))

            efficiency_plot = go.Figure()
            efficiency_plot.add_trace(go.Bar(x=stock_data['year'], y=stock_data['ROA %'],
                                             name='ROA', marker=dict(color='#154e8c')))
            efficiency_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['ROA %'],
                                          mode='lines+markers', showlegend=False,
                                          line=dict(shape='spline', smoothing=1, width=3, color='#ec5924')))
            efficiency_plot.update_layout(xaxis_title="Năm",
                                          yaxis_title="%",
                                          plot_bgcolor='white',
                                          paper_bgcolor='white',
                                          xaxis=dict(showgrid=False),
                                          yaxis=dict(showgrid=True, gridcolor='lightgray'))

            eps_plot = go.Figure()
            eps_plot.add_trace(go.Bar(x=stock_data['year'], y=stock_data['EPS'],
                                      name='EPS', marker=dict(color='#154e8c')))
            eps_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['EPS'],
                                          mode='lines+markers', showlegend=False,
                                          line=dict(shape='spline', smoothing=1, width=3, color='#ec5924')))
            eps_plot.update_layout(xaxis_title="Năm",
                                   yaxis_title="Triệu đồng",
                                   plot_bgcolor='white',
                                   paper_bgcolor='white',
                                   xaxis=dict(showgrid=False),
                                   yaxis=dict(showgrid=True, gridcolor='lightgray'))

            bvps_plot = go.Figure()
            bvps_plot.add_trace(go.Bar(x=stock_data['year'], y=stock_data['BVPS'],
                                       name='BVPS', marker=dict(color='#154e8c')))
            bvps_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['BVPS'],
                                           mode='lines+markers', showlegend=False,
                                           line=dict(shape='spline', smoothing=1, width=3, color='#ec5924')))
            bvps_plot.update_layout(xaxis_title="Năm",
                                    yaxis_title="Triệu đồng",
                                    plot_bgcolor='white', paper_bgcolor='white',
                                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='lightgray'))

            pe_plot = go.Figure()
            pe_plot.add_trace(go.Bar(x=stock_data['year'], y=stock_data['P/E'],
                                     name='P/E', marker=dict(color='#154e8c')))
            pe_plot.add_trace(go.Scatter(x=stock_data['year'], y=stock_data['P/E'],
                                         mode='lines+markers', showlegend=False,
                                         line=dict(shape='spline', smoothing=1, width=3, color='#ec5924')))
            pe_plot.update_layout(xaxis_title="Năm",
                                  yaxis_title="Triệu đồng",
                                  plot_bgcolor='white', paper_bgcolor='white',
                                  xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='lightgray'))

            # Chuyển các biểu đồ thành HTML
            liquidity_plot_html = liquidity_plot.to_html(full_html=False)
            leverage_plot_html = leverage_plot.to_html(full_html=False)
            efficiency_plot_html = efficiency_plot.to_html(full_html=False)
            eps_plot_html = eps_plot.to_html(full_html=False)
            bvps_plot_html = bvps_plot.to_html(full_html=False)
            pe_plot_html = pe_plot.to_html(full_html=False)

            return render_template_string(html_template,
                                          stock_code=stock_code,
                                          liquidity_plot=liquidity_plot_html,
                                          leverage_plot=leverage_plot_html,
                                          efficiency_plot=efficiency_plot_html,
                                          eps_plot=eps_plot_html,
                                          bvps_plot=bvps_plot_html,
                                          pe_plot=pe_plot_html,
                                          cluster_table=cluster_table_html,
                                          cluster_cards=cluster_cards_html)

        else:
            result = "Không tìm thấy mã cổ phiếu"

    return render_template_string(html_template, result=result)

if __name__ == "__main__":
    app.run(debug=True)
