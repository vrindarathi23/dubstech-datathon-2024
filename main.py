import numpy as np
import pandas as pd


# Loading and cleaning data
df = pd.read_csv('UrbanEdgeApparel.csv')
df = df.sort_values(by='Product ID')
df = df.dropna(subset=[
    'Product ID', 'Customer ID', 'Product Quantity', 'Order Status',
    'Total Selling Price'
])
kpis = pd.DataFrame()


# First KPI: total number of units in baskets for each product
total_sales = df.groupby('Product ID')['Product Quantity'].sum()
kpis['Total Sales'] = total_sales


# Second KPI: total revenue generated for each product
total_revenue = df.groupby('Product ID')['Total Selling Price'].sum()
kpis['Total Revenue'] = total_revenue


# Third KPI: ratio of completed/processed orders to total orders
completed_df = df[(df['Order Status'] == 'Completed') |
                  (df['Order Status'] == 'Process')]
completed = completed_df.groupby('Product ID').size()

total = df.groupby('Product ID').size()
completion_rate = completed / total
kpis['Completion Rate'] = completion_rate


# Fourth KPI: sales growth from 2021 to 2023
yr_2021 = df[df['Order Year'] == 2021]
revenue_2021 = yr_2021.groupby('Product ID')['Total Selling Price'].sum()
yr_2023 = df[df['Order Year'] == 2023]
revenue_2023 = yr_2023.groupby('Product ID')['Total Selling Price'].sum()

prod_2021 = yr_2021.groupby('Product ID').size()
prod_2023 = yr_2023.groupby('Product ID').size()

revenue_2021, revenue_2023 = revenue_2021.align(revenue_2023, fill_value=0)
sales_growth = (revenue_2023 - revenue_2021) / revenue_2021.replace(0, np.nan)
sales_growth = pd.Series(sales_growth, index=revenue_2021.index)
kpis['Sales Growth'] = sales_growth
kpis['Sales Growth'] = kpis['Sales Growth'].fillna(0)


# Fifth KPI: ratio of repurchase customers to total customers
distinct_orders = df.groupby(['Customer ID', 'Product ID'
                              ])['Order ID'].nunique().reset_index()
distinct_orders = distinct_orders.rename(
    columns={'Order ID': 'Distinct Orders'})
distinct_orders['Reorder'] = (distinct_orders['Distinct Orders']
                              > 1).astype(int)
reorders = distinct_orders.groupby('Product ID')['Reorder'].sum().reset_index()
reorders = reorders.rename(columns={'Reorder': 'Reorders'})

unique_cust = df.groupby('Product ID')['Customer ID'].nunique().reset_index()
unique_cust = unique_cust.rename(columns={'Customer ID': 'Unique Customers'})

repurchase_df = pd.merge(reorders, unique_cust, on='Product ID')
repurchase_df['Rate'] = (repurchase_df['Reorders'] /
                         repurchase_df['Unique Customers'])
repurchase_df.reset_index(drop=True, inplace=True)
repurchase_df.set_index('Product ID', inplace=True)
kpis['Repurchase Rate'] = repurchase_df['Rate']


# Combining results to find final score for each product
kpis = kpis.sort_values(by='Repurchase Rate', ascending=False)
kpis['Metric'] = kpis['Total Sales'] + kpis['Total Revenue'] + (
    1000 * kpis['Completion Rate']) + (1000 * kpis['Sales Growth']) + (
        1000 * kpis['Repurchase Rate'])
kpis = kpis.sort_values(by='Metric', ascending=False)
kpis.to_csv('metrics.csv')
