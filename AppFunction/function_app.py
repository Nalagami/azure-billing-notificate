import logging

import azure.functions as func

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 9 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def billingNotificate(myTimer: func.TimerRequest) -> None:
    import math
    import os
    import pprint
    import time
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    import pandas as pd
    import requests
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.costmanagement.models import QueryTimePeriod

    # 請求アカウントID
    BILLING_ACCOUNT_ID = os.environ["BILLING_ACCOUNT_ID"]
    WEBHOOK_URL = os.environ["WEBHOOK_URL"]

    # CostManagementを操作するための認証情報を取得
    def GetCostManagementObject():
        # Acquire a credential object
        return CostManagementClient(DefaultAzureCredential())

    # SCOPEの定義
    def define_scope():
        return f"/providers/Microsoft.Billing/billingAccounts/{BILLING_ACCOUNT_ID}"

    # Time_Periodの定義
    def define_period(fm_tp, to_tp):
        fm_datetime = fm_tp
        to_datetime = to_tp
        def_period = QueryTimePeriod(from_property=fm_datetime, to=to_datetime)
        return def_period

    # クエリの定義
    def define_query(fm_tp, to_tp):
        # データ取得期間の定義
        def_period = define_period(fm_tp, to_tp)

        # クエリの作成
        return {
            "type": "Usage",
            "timeframe": "Custom",
            "time_period": def_period,
            "dataset": {
                "granularity": "None",
                "aggregation": {
                    "totalCost": {"name": "PreTaxCost", "function": "Sum"},
                    "totalQuantity": {"name": "UsageQuantity", "function": "Sum"},
                },
                "grouping": [
                    # {"type": "Dimension", "name": "ResellerMPNId"},
                    # {"type": "Dimension", "name": "InvoiceId"},
                    # {"type": "Dimension", "name": "ResourceGroup"},
                    {"type": "Dimension", "name": "ServiceFamily"},
                    {"type": "Dimension", "name": "ServiceName"},
                    # {"type": "Dimension", "name": "MeterCategory"},
                    # {"type": "Dimension", "name": "Meter"},
                    # # {"type": "Dimension", "name": "MeterSubcategory"},
                    # {"type": "Dimension", "name": "Product"},
                    # {"type": "Dimension", "name": "UnitOfMeasure"},
                    # {"type": "Dimension", "name": "ProductOrderName"}
                ],
            },
        }

    # 指定した Subscription について CostManagement からコストを取得
    def GetCostManagement(fm_tp, to_tp):
        # CostManagementから請求データの取得
        try:
            # CostManagementを操作するオブジェクトの取得
            client = GetCostManagementObject()

            # SCOPEの定義
            def_scope = define_scope()

            # クエリの定義
            def_query = define_query(fm_tp, to_tp)
            costmanagement = client.query.usage(scope=def_scope, parameters=def_query)
        except Exception as e:
            logging.error(e)
            Exception("Error ---> CostManagementから請求データの取得に失敗しました。")
        finally:
            client.close()
        return costmanagement

    # とある顧客の指定した期間でもCostManagement情報を取得
    def GetCustomerCsotManagement(fm_tp, to_tp):
        # CostManagement からコストを取得
        costmanagement = GetCostManagement(fm_tp, to_tp)

        # columnsデータを取得
        columns = list(map(lambda col: col.name, costmanagement.columns))

        # rowsデータを取得
        rows = costmanagement.rows

        # 請求データをDataframe型で取得
        df_cost = pd.DataFrame(rows, columns=columns)

        return df_cost

    # dataframeをmapの配列に変換する関数
    def converte_dataframe_to_map(df):
        map_array = []
        for col in df.columns:
            map_array.append(df[col].map(lambda x: x * 2).tolist())
        pprint.pprint(map_array)
        return map_array

    # 取得した全データの画面出力
    def data_to_display(df_cost):
        # 取得した全データの表示
        logging.info(data_format(df_cost))

    # 取得した全データの整形
    def data_format(df_cost):
        df_cost = df_cost.drop(columns=["Currency"])
        return df_cost.to_markdown()

    # 取得した全データの保存
    def data_to_csv(df_cost):
        # 取得した全データのcsvファイルへ保存
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        filename = "./cost_by_" + now.strftime("%Y%m%d%H%M%S") + ".csv"
        logging.info(filename)
        df_cost.to_csv(filename, index=False, encoding="utf-8")

    # データ取得のための From-To 日付確認
    def check_time_period(fm_tp, to_tp):
        try:
            fm_datetime = datetime.strptime(fm_tp, "%Y-%m-%d")
            to_datetime = datetime.strptime(to_tp, "%Y-%m-%d")

            if to_datetime < fm_datetime:
                logging.error("Error ---> 開始日 ≦ 終了日 ")
                return False
            else:
                return True
        except ValueError as e:
            logging.error("ValueError = ", e)
            return False

    def get_first_date(dt):
        return dt.replace(day=1)

    def post_slack_message(message: str, WEBHOOK_URL) -> None:
        headers = {"Content-type": "application/json"}
        data = {"text": message}
        requests.post(WEBHOOK_URL, headers=headers, json=data)

    # 今月の初日 ~ 投稿日前日まででクエリする
    # 月初だったら0円固定で通知する
    def main():
        today = datetime.now()

        # 月初だったら処理を停止
        if today == get_first_date(today):
            return

        # start_date
        start_date = get_first_date(today)

        # end_date
        end_date = today - timedelta(1)

        start = time.time()
        df_cost = GetCustomerCsotManagement(start_date, end_date)

        # TODO:[{サービス名: ,料金: }] の形にdataframeを変換する関数を作る

        # 取得した全データを出力
        data_to_display(df_cost)

        # 合計請求金額と件数の表示
        total = math.floor(df_cost["PreTaxCost"].sum() * 100) / 100
        count = len(df_cost)
        logging.info(
            "\n",
            f"合計請求金額 : {total}",
            "\tデータ件数 : {:,.0f}".format(count),
        )

        generate_time = time.time() - start
        logging.info("\n 取得時間:{0}".format(generate_time) + " [sec] \n")

        # slackにメッセージを送信する
        post_slack_message(
            f"{data_format(df_cost)}\n\n" + f"合計金額：{total} JPY", WEBHOOK_URL
        )

    # メイン処理
    if myTimer.past_due:
        logging.info("The timer is past due!")

    main()

    logging.info("Python timer trigger function executed.")
