import os
import requests
import dotenv

dotenv.load_dotenv()

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools


class FlightSearch(Tools):
    """
    FlightSearch 类是一个工具，使用 AviationStack API 根据航班号查询航班信息。
    """

    def __init__(self, api_key: str = None):
        """
        初始化 FlightSearch 工具，获取 API 密钥。
        参数:
            api_key (str): 如果没有提供 API 密钥，将从环境变量中加载
        """
        super().__init__()
        self.tag = "flight_search"
        self.api_key = api_key or os.getenv("AVIATIONSTACK_API_KEY")  # 从环境变量获取 API 密钥

    def execute(self, blocks: str, safety: bool = True) -> str:
        """
        执行航班查询操作。
        参数:
            blocks (str): 包含航班号的字符串
            safety (bool): 是否进行安全确认
        返回:
            str: 返回航班信息或错误消息
        """
        if self.api_key is None:
            return "错误: 没有提供 AviationStack API 密钥。"

        for block in blocks:
            flight_number = block.strip()  # 获取航班号
            if not flight_number:
                return "错误: 没有提供航班号。"

            try:
                url = "http://api.aviationstack.com/v1/flights"  # AviationStack API URL
                params = {
                    "access_key": self.api_key,
                    "flight_iata": flight_number,  # IATA 航班号
                    "limit": 1  # 限制返回一个结果
                }
                response = requests.get(url, params=params)  # 发送 GET 请求
                response.raise_for_status()  # 如果请求失败，抛出异常

                data = response.json()  # 解析 JSON 响应
                if "data" in data and len(data["data"]) > 0:
                    flight = data["data"][0]  # 获取第一个航班的数据
                    # 提取关键航班信息
                    flight_status = flight.get("flight_status", "未知")
                    departure = flight.get("departure", {})
                    arrival = flight.get("arrival", {})
                    airline = flight.get("airline", {}).get("name", "未知")

                    departure_airport = departure.get("airport", "未知")
                    departure_time = departure.get("scheduled", "未知")
                    arrival_airport = arrival.get("airport", "未知")
                    arrival_time = arrival.get("scheduled", "未知")

                    return (
                        f"航班: {flight_number}\n"
                        f"航空公司: {airline}\n"
                        f"状态: {flight_status}\n"
                        f"起飞: {departure_airport} 于 {departure_time}\n"
                        f"到达: {arrival_airport} 于 {arrival_time}"
                    )
                else:
                    return f"没有找到航班 {flight_number} 的信息"
            except requests.RequestException as e:
                return f"航班查询出错: {str(e)}"
            except Exception as e:
                return f"意外错误: {str(e)}"
        return "没有执行航班查询"

    def execution_failure_check(self, output: str) -> bool:
        """
        检查航班查询操作是否失败。
        参数:
            output (str): 执行结果
        返回:
            bool: 如果执行失败，返回 True，否则返回 False
        """
        return output.startswith("错误") or "没有找到航班信息" in output

    def interpreter_feedback(self, output: str) -> str:
        """
        提供航班查询操作的反馈。
        参数:
            output (str): 执行结果
        返回:
            str: AI 的反馈消息
        """
        if self.execution_failure_check(output):  # 如果查询失败，返回错误信息
            return f"航班查询失败: {output}"
        return f"航班信息:\n{output}"  # 返回查询结果


if __name__ == "__main__":
    flight_tool = FlightSearch()  # 创建 FlightSearch 实例
    flight_number = "AA123"  # 示例航班号
    result = flight_tool.execute([flight_number], safety=True)  # 执行航班查询
    feedback = flight_tool.interpreter_feedback(result)  # 获取反馈
    print(feedback)  # 输出反馈
