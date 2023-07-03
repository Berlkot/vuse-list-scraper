from bs4 import BeautifulSoup
import aiohttp
import json
import asyncio
import ssl
import certifi

# 0 - снилс 1 - баллы 2 - приоритет 4 - оригинал


def iter_data(data, indices):
    for i in indices:
        value: str = data[i]
        if value.isdigit():
            yield i, int(value)


def has_any_humber(string: str):
    for i in string:
        if i.isdigit():
            return True
    return False


def join_result(data):
    out = ""
    for i in data:
        if i == 0 or i == 1000:
            out += ","
        else:
            out += "," + str(i)
    return out[1:]


def join_average_result(data):
    out = ""
    for i in data:
        if i == 0:
            out += ","
        else:
            out += "," + str(i[1]//i[0])
    return out[1:]


class GathererData:
    def __init__(self, config, mapping):
        self.mapping = mapping
        self.config = config
        self.site_specials = config["site_specials"]
        self.csv_data = ""
        self.row_data_length = [0 for _ in self.config["track_values"]]
        self.compute_data = None

    def compute_sum(self, data):
        for i, value in iter_data(data, self.config["compute_sum"]):
            self.compute_data["sum"][i] += value

    def compute_average(self, data):
        for i, value in iter_data(data, self.config["compute_average"]):
            if isinstance(self.compute_data["average"][i], list):
                self.compute_data["average"][i][0] += 1
                self.compute_data["average"][i][1] += value
            else:
                self.compute_data["average"][i] = [1, value]

    def compute_max(self, data):
        for i, value in iter_data(data, self.config["compute_max"]):
            self.compute_data["max"][i] = max(value, self.compute_data["max"][i])

    def compute_min(self, data):
        for i, value in iter_data(data, self.config["compute_min"]):
            if value > 0:
                self.compute_data["min"][i] = min(value, self.compute_data["min"][i])

    def mask_url(self, url):
        pass

    async def calculate_data(self):
        self.csv_data += ",," + ",".join(self.config["track_values"]) + "\n"
        ind = 0
        for uni in self.mapping:
            self.csv_data += uni + "\n\n"
            for index, table in enumerate(self.mapping[uni]):
                self.compute_data = {
                    "sum": self.row_data_length.copy(),
                    "average": self.row_data_length.copy(),
                    "max": self.row_data_length.copy(),
                    "min": [1000 for _ in self.config["track_values"]]
                }

                if ind < len(self.config["url_masking"]):
                    st = self.config["url_masking"][ind]
                else:
                    st = self.config["url_mapping"][uni][index][0]
                self.csv_data += "," + st + "\n"
                ind += 1
                for row in table:
                    try:
                        data = []
                        for i in self.config["track_values"]:
                            if self.site_specials[uni].get(i, None) is not None:
                                data.append(row[self.site_specials[uni][i]])
                            else:
                                data.append("Err: N/A")
                    except IndexError:
                        continue
                    for j_index, cell in enumerate(data):
                        if self.site_specials[uni]["true"] == cell:
                            data[j_index] = "1"
                        if self.site_specials[uni]["false"] == cell:
                            data[j_index] = "0"
                    self.csv_data += ",," + ",".join(data) + "\n"
                    self.compute_sum(data)
                    self.compute_average(data)
                    self.compute_max(data)
                    self.compute_min(data)
                for i in self.compute_data:
                    if i == "average":
                        st = join_average_result(self.compute_data[i])
                    else:
                        st = join_result(self.compute_data[i])
                    self.csv_data += f",{self.config['compute_names'][i]}:," + st + "\n"
                self.csv_data += "\n"
            self.csv_data += "\n"

    def write_to_csv(self):
        with open("./result.csv", "w") as f:
            f.write(self.csv_data)


class Gatherer:
    def __init__(self, config):
        self.mapping = config["url_mapping"].copy()
        self.site_specials = config["site_specials"]
        # save all config data for top level lists
        self.config = config

    @staticmethod
    async def parse_data(text: str):
        students = []
        soup = BeautifulSoup(text, "html.parser")
        items = soup.find_all("table")[0]
        for column in items.find_all_next("tr"):
            if not has_any_humber(column.find_next("td").text):
                continue
            tmp = []
            for cell in column.contents:
                tmp.append(cell.text.strip())
            students.append(tmp)
        return students

    @staticmethod
    async def create_session(url):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context)
        kwargs = {}
        for i in url:
            kwargs[i] = url[i]
        return aiohttp.ClientSession(connector=conn, **kwargs)

    async def get_response(self, uni: str, url):
        session = await self.create_session(url[2:])
        query_type = self.site_specials[uni]["request_type"]
        match query_type:
            case "GET":
                response = await session.get(url[0])
            case "POST":
                if url[1]:
                    response = await session.post(url[0], data=url[1])
                else:
                    response = await session.post(url[0])
        text = await response.text()
        await session.close()
        return uni, await self.parse_data(text)

    async def gather_tables(self):
        results = []
        async with asyncio.TaskGroup() as tg:
            for uni in self.mapping:
                results.append([tg.create_task(self.get_response(uni, link)) for link in self.mapping[uni]])
        for uni in results:
            tmp = []
            result = None
            for table in uni:
                result = table.result()
                tmp.append(result[1])
            if result:
                self.mapping[result[0]] = tmp
        return GathererData(self.config, self.mapping)


async def main():
    with open("./config.json") as f:
        config = json.load(f)
        gatherer = Gatherer(config)
        data = await gatherer.gather_tables()
        await data.calculate_data()
        data.write_to_csv()


if __name__ == "__main__":
    asyncio.run(main())
