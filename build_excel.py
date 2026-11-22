import sqlite3, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.formatting.rule import CellIsRule
con=sqlite3.connect("data/sales.db"); con.executescript(open("sql/kpi_queries.sql").read().split("-- Q01")[0])
R="data/results/"
mon=pd.read_sql("SELECT ym, yr, SUM(revenue) revenue, SUM(profit) profit, COUNT(DISTINCT order_id) orders FROM v_sales GROUP BY ym, yr ORDER BY ym",con)
reg=pd.read_sql("SELECT region_name, yr, SUM(revenue) revenue, SUM(profit) profit, COUNT(DISTINCT order_id) orders FROM v_sales GROUP BY region_name, yr",con)
mon["yr"]=mon.yr.astype(int); reg["yr"]=reg.yr.astype(int)
cat=pd.read_sql("SELECT category, SUM(revenue) revenue, SUM(profit) profit FROM v_sales GROUP BY category ORDER BY revenue DESC",con)
fc=pd.read_csv(R+"forecast_total.csv"); fr=pd.read_csv(R+"forecast_region.csv")
F="Arial"; NAVY="1F3A5F"; ORG="E07A1F"; GREY="F2F4F7"
hf=Font(name=F,bold=True,color="FFFFFF"); hfill=PatternFill("solid",fgColor=NAVY)
def sheet_df(ws,df,fmts):
    for j,c in enumerate(df.columns,1):
        x=ws.cell(1,j,c); x.font=hf; x.fill=hfill; x.alignment=Alignment(horizontal="center")
        ws.column_dimensions[x.column_letter].width=16
    for i,row in enumerate(df.itertuples(index=False),2):
        for j,v in enumerate(row,1):
            x=ws.cell(i,j,v); x.font=Font(name=F)
            if df.columns[j-1] in fmts: x.number_format=fmts[df.columns[j-1]]
    ws.freeze_panes="A2"
wb=Workbook(); d=wb.active; d.title="Dashboard"
m=wb.create_sheet("Monthly"); sheet_df(m,mon,{"revenue":"$#,##0","profit":"$#,##0","orders":"#,##0"})
r=wb.create_sheet("Regions"); sheet_df(r,reg,{"revenue":"$#,##0","profit":"$#,##0","orders":"#,##0"})
c=wb.create_sheet("Categories"); sheet_df(c,cat,{"revenue":"$#,##0","profit":"$#,##0"})
# Trend: actual + forecast aligned
t=wb.create_sheet("Trend")
for j,h in enumerate(["Month","Actual revenue","Forecast","Lower 80%","Upper 80%"],1):
    x=t.cell(1,j,h); x.font=hf; x.fill=hfill; t.column_dimensions[x.column_letter].width=16
for i,row in enumerate(mon.itertuples(),2):
    t.cell(i,1,row.ym); t.cell(i,2,f"=INDEX(Monthly!$C:$C,MATCH(A{i},Monthly!$A:$A,0))")
n=len(mon)+1
t.cell(n,3,f"=B{n}")  # join forecast line to last actual
for k,row in enumerate(fc.itertuples(),n+1):
    t.cell(k,1,row.month); t.cell(k,3,row.forecast); t.cell(k,4,row.lower_80); t.cell(k,5,row.upper_80)
for row in t.iter_rows(min_row=2):
    for x in row: x.font=Font(name=F); x.number_format="@" if x.column==1 else "$#,##0"
t.cell(n+len(fc)+3,1,"Forecast: Holt-Winters (additive trend, multiplicative seasonality), see notebooks/sales_forecasting.ipynb. Values are pasted model output (hardcoded).").font=Font(name=F,italic=True,size=9)
# Region forecast table
rf=wb.create_sheet("RegionForecast")
rows=fr.groupby("region").forecast.sum().reset_index()
for j,h in enumerate(["Region","2025 actual","2026 forecast","YoY %","Status"],1):
    x=rf.cell(1,j,h); x.font=hf; x.fill=hfill; rf.column_dimensions[x.column_letter].width=16
for i,row in enumerate(rows.itertuples(),2):
    rf.cell(i,1,row.region); rf.cell(i,2,f'=SUMIFS(Regions!$C:$C,Regions!$A:$A,A{i},Regions!$B:$B,2025)')
    rf.cell(i,3,round(row.forecast)); rf.cell(i,4,f"=C{i}/B{i}-1"); rf.cell(i,5,f'=IF(D{i}<0,"Underperforming","On track")')
    for j,f_ in zip(range(1,6),[None,"$#,##0","$#,##0","0.0%",None]):
        rf.cell(i,j).font=Font(name=F); 
        if f_: rf.cell(i,j).number_format=f_
# ---- Dashboard
d.sheet_view.showGridLines=False
for col,w in zip("ABCDEFGHIJKLMN",[2]+[15]*13): d.column_dimensions[col].width=w
d["B1"]="Regional Sales Dashboard"; d["B1"].font=Font(name=F,size=20,bold=True,color=NAVY)
d["B2"]="SYNTHETIC data (seeded generator) for portfolio use, 2023-2025. Revenue = qty x price x (1 - discount)."; d["B2"].font=Font(name=F,size=9,italic=True,color="666666")
kp=[("Total revenue","=SUM(Monthly!C:C)","$#,##0.0,,\"M\""),("Total profit","=SUM(Monthly!D:D)","$#,##0.0,,\"M\""),
    ("Profit margin","=D4/B4","0.0%"),("Orders","=SUM(Monthly!E:E)","#,##0"),
    ("Avg order value","=B4/E4","$#,##0.00"),("2025 YoY growth",'=SUMIFS(Monthly!C:C,Monthly!B:B,2025)/SUMIFS(Monthly!C:C,Monthly!B:B,2024)-1',"0.0%")]
cols=["B","D","F","H","J","L"]
thin=Side(style="thin",color="D0D5DD")
for (lab,f_,nf),col in zip(kp,cols):
    ci=ord(col)-64
    d.merge_cells(start_row=3,start_column=ci,end_row=3,end_column=ci+1); d.merge_cells(start_row=4,start_column=ci,end_row=4,end_column=ci+1)
    a=d[f"{col}3"]; a.value=lab; a.font=Font(name=F,size=9,color="666666"); a.alignment=Alignment(horizontal="center")
    b=d[f"{col}4"]; b.value=f_; b.number_format=nf; b.font=Font(name=F,size=18,bold=True,color=NAVY); b.alignment=Alignment(horizontal="center")
    for rr in (3,4):
        for cc in (ci,ci+1): d.cell(rr,cc).fill=PatternFill("solid",fgColor=GREY)
d.row_dimensions[4].height=32
# fix KPI refs: margin uses profit (D4) / revenue (B4); AOV uses B4/ orders at H4
d["F4"]="=D4/B4"; d["J4"]="=B4/H4"
# Region table
d["B6"]="Regional performance"; d["B6"].font=Font(name=F,bold=True,size=12,color=NAVY)
hd=["Region","Revenue","Margin","2025 YoY","2026 forecast","Status"]
for j,h in enumerate(hd):
    x=d.cell(7,2+j,h); x.font=hf; x.fill=hfill; x.alignment=Alignment(horizontal="center")
regs=list(rows.region)
for i,g in enumerate(regs,8):
    d.cell(i,2,g)
    d.cell(i,3,f'=SUMIFS(Regions!$C:$C,Regions!$A:$A,B{i})')
    d.cell(i,4,f'=SUMIFS(Regions!$D:$D,Regions!$A:$A,B{i})/C{i}')
    d.cell(i,5,f'=SUMIFS(Regions!$C:$C,Regions!$A:$A,B{i},Regions!$B:$B,2025)/SUMIFS(Regions!$C:$C,Regions!$A:$A,B{i},Regions!$B:$B,2024)-1')
    d.cell(i,6,f'=INDEX(RegionForecast!$C:$C,MATCH(B{i},RegionForecast!$A:$A,0))')
    d.cell(i,7,f'=IF(E{i}<0,"Underperforming","On track")')
    for j,nf in zip(range(2,8),[None,"$#,##0","0.0%","0.0%","$#,##0",None]):
        d.cell(i,j).font=Font(name=F)
        if nf: d.cell(i,j).number_format=nf
        d.cell(i,j).border=Border(bottom=thin)
last=7+len(regs)
d.conditional_formatting.add(f"E8:E{last}",CellIsRule(operator="lessThan",formula=["0"],font=Font(name=F,color="C0392B",bold=True)))
d.conditional_formatting.add(f"G8:G{last}",CellIsRule(operator="equal",formula=['"Underperforming"'],font=Font(name=F,color="C0392B",bold=True)))
d.column_dimensions["G"].width=18
# Charts
lc=LineChart(); lc.title="Monthly revenue and 12-month forecast"; lc.height=8; lc.width=17
lc.add_data(Reference(t,min_col=2,min_row=1,max_row=n+len(fc)),titles_from_data=True)
lc.add_data(Reference(t,min_col=3,min_row=1,max_row=n+len(fc)),titles_from_data=True)
lc.set_categories(Reference(t,min_col=1,min_row=2,max_row=n+len(fc)))
lc.series[0].graphicalProperties.line.solidFill=NAVY; lc.series[1].graphicalProperties.line.solidFill=ORG; lc.series[1].graphicalProperties.line.dashStyle="dash"
for s_ in lc.series: s_.smooth=False; s_.graphicalProperties.line.width=22000
lc.y_axis.number_format='$#,##0.0,,"M"'; lc.y_axis.title="Revenue"; lc.x_axis.tickLblSkip=3; lc.x_axis.number_format="@"
lc.roundedCorners=False; lc.legend.position="b"; lc.legend.overlay=False; lc.title.overlay=False; lc.y_axis.title.overlay=False
lc.x_axis.delete=False; lc.y_axis.delete=False
d.add_chart(lc,"B15")
bc=BarChart(); bc.type="col"; bc.title="Revenue by category"; bc.height=8; bc.width=13
bc.add_data(Reference(c,min_col=2,min_row=1,max_row=len(cat)+1),titles_from_data=True); bc.set_categories(Reference(c,min_col=1,min_row=2,max_row=len(cat)+1))
bc.series[0].graphicalProperties.solidFill=NAVY; bc.y_axis.number_format='$#,##0,,"M"'; bc.legend=None
bc.roundedCorners=False; bc.title.overlay=False; bc.x_axis.delete=False; bc.y_axis.delete=False
d.add_chart(bc,"I15")
rb=BarChart(); rb.type="col"; rb.title="2025 actual vs 2026 forecast by region"; rb.height=8; rb.width=17
rb.add_data(Reference(rf,min_col=2,max_col=3,min_row=1,max_row=len(rows)+1),titles_from_data=True); rb.set_categories(Reference(rf,min_col=1,min_row=2,max_row=len(rows)+1))
rb.series[0].graphicalProperties.solidFill="9AA5B1"; rb.series[1].graphicalProperties.solidFill=ORG; rb.y_axis.number_format='$#,##0,,"M"'
rb.roundedCorners=False; rb.legend.position="b"; rb.legend.overlay=False; rb.title.overlay=False; rb.x_axis.delete=False; rb.y_axis.delete=False
d.add_chart(rb,"B32")
d["I32"]="Insight"; d["I32"].font=Font(name=F,bold=True,size=12,color=NAVY)
notes=["Revenue is strongly seasonal: summer and Nov-Dec peaks.","Central is the only shrinking region and is flagged for a recovery plan.","Electronics drives volume but has the lowest margin; Fashion and Beauty carry the margin.","Deep discounts (20%) cut margin sharply; see SQL Q10."]
for i,s_ in enumerate(notes,33):
    d.cell(i,9,"- "+s_).font=Font(name=F,size=10)
d.page_setup.orientation="landscape"; d.page_setup.fitToWidth=1; d.page_setup.fitToHeight=0; d.sheet_properties.pageSetUpPr=PageSetupProperties(fitToPage=True)
wb.save("excel/sales_dashboard.xlsx")
