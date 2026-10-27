# Build the dashboard in Tableau Public (free)

Task 3 allows Matplotlib, Seaborn **or** Tableau. The Python charts are already done; use this guide to recreate the dashboard in Tableau for your portfolio. Expect about 45 minutes.

## 0. Setup
1. Download **Tableau Public** (free) from public.tableau.com and sign in.
2. Open it, choose **Connect > Text file**, and select `data/retail_sales.csv`.
3. Check the data types on the Data Source tab: `order_date` = Date, `sales`, `profit`, `discount` = Number (decimal), the rest = String.

## 1. Calculated fields (Analysis > Create Calculated Field)
| Name | Formula |
|---|---|
| Profit Margin | `SUM([profit]) / SUM([sales])` |
| Discount Band | `IF [discount] <= 0.1 THEN "0-10%" ELSEIF [discount] <= 0.2 THEN "11-20%" ELSEIF [discount] < 0.3 THEN "21-29%" ELSE "30%+" END` |
| Loss Order | `IF [profit] < 0 THEN 1 ELSE 0 END` |

## 2. Build these sheets
Name each sheet exactly as shown.

1. **KPIs** - drag `Measure Names` to Rows, filter to Sales, Profit, Profit Margin; set Marks to Text. Or make one sheet per KPI with a big number.
2. **Revenue Trend** - Columns: `order_date` (right-click > Month, continuous). Rows: `SUM(sales)`. Add a trend line or a 3-month moving average (right-click the measure > Quick Table Calculation > Moving Average, 3 periods). Title: *Revenue grows each year, with sharp year-end peaks*.
3. **Category Performance** - Rows: `category`; Columns: `SUM(sales)`. Drag `Profit Margin` to Label. Sort descending. Color by category (blue, orange, green).
4. **Margin Heatmap** - Columns: `category`; Rows: `region`. Marks: Square. Color: `Profit Margin` with a **diverging** palette (Edit Colors > Red-Blue Diverging, Use Full Color Range off, Center = 0). Label: `Profit Margin`.
5. **Discount vs Margin** - Columns: `Discount Band`; Rows: `Profit Margin`. Drag `category` to Color. Add a reference line at 0.
6. **Seasonality** - Columns: `MONTH(order_date)`; Rows: `YEAR(order_date)`. Marks: Square, Color: `SUM(sales)` with a single-hue blue sequential palette.

## 3. Assemble the dashboard
1. Dashboard > New Dashboard, size **Automatic** or 1400 x 900.
2. Layout: KPIs across the top, Revenue Trend and Category Performance in the middle row, Margin Heatmap and Discount vs Margin in the bottom row.
3. Add filters for `region` and `year` (Show Filter on a sheet, then **Apply to Worksheets > Selected Worksheets** and pick all). Use dashboard actions (Dashboard > Actions > Filter) so clicking a bar filters the other charts.
4. Add a text box title: **Retail Sales Dashboard 2023-2025**, and a one-line takeaway: *Discounts of 30%+ turn profit negative, with Furniture hit hardest.*

## 4. Design checklist
- Titles state the finding, not the topic.
- Same color per category on every sheet.
- Hide unneeded gridlines and borders; keep axis labels short.
- Use tooltips to show margin and sales together.

## 5. Publish
File > Save to Tableau Public, then copy the public link into the README (replace the placeholder at the bottom) and your resume or LinkedIn.
