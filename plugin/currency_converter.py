import decimal
import locale
import requests
import json
from flox import Flox
from typing import List, Dict

class Currency(Flox):
    locale.setlocale(locale.LC_ALL, "")
    ratesURL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.json"
    
    # Define ALLOWED_CURRENCIES set here with all the currencies you provided (in lowercase)
    ALLOWED_CURRENCIES = {
        "aed", "afn", "all", "amd", "ang", "aoa", "ars", "aud", "awg", "azn",
        "bam", "bbd", "bdt", "bgn", "bhd", "bif", "bmd", "bnd", "bob", "brl",
        "bsd", "btn", "bwp", "byn", "bzd", "cad", "cdf", "chf", "clp", "cny",
        "cop", "crc", "cuc", "cup", "cve", "czk", "djf", "dkk", "dop", "dzd",
        "egp", "ern", "etb", "eur", "fjd", "fkp", "gbp", "gel", "ggp", "ghs",
        "gip", "gmd", "gnf", "gtq", "gyd", "hkd", "hnl", "hrk", "htg", "huf",
        "idr", "ils", "imp", "inr", "iqd", "irr", "isk", "jep", "jmd", "jod",
        "jpy", "kes", "kgs", "khr", "kmf", "kpw", "krw", "kwd", "kyd", "kzt",
        "lak", "lbp", "lkr", "lrd", "lsl", "lyd", "mad", "mdl", "mga", "mkd",
        "mmk", "mnt", "mop", "mru", "mur", "mvr", "mwk", "mxn", "myr", "mzn",
        "nad", "ngn", "nio", "nok", "npr", "nzd", "omr", "pab", "pen", "pgk",
        "php", "pkr", "pln", "pyg", "qar", "ron", "rsd", "rub", "rwf", "sar",
        "sbd", "scr", "sdg", "sek", "sgd", "shp", "sll", "sos", "spl", "srd",
        "stn", "svc", "syp", "szl", "thb", "tjs", "tmt", "tnd", "top", "try",
        "ttd", "tvd", "twd", "tzs", "uah", "ugx", "usd", "uyu", "uzs", "vef",
        "vnd", "vuv", "wst", "xaf", "xcd", "xdr", "xof", "xpf", "yer", "zar",
        "zmw", "zwd"
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_age = self.settings.get("max_age")
        self.logger_level("info")
        self.CURRENCIES = self.get_available_currencies()

    def get_available_currencies(self) -> List[str]:
        try:
            response = requests.get(self.ratesURL)
            if response.status_code == 200:
                data = response.json()
                currencies = [curr.upper() for curr in data['eur'].keys() 
                            if curr in self.ALLOWED_CURRENCIES]
                if 'EUR' not in currencies:
                    currencies.append('EUR')
                return sorted(currencies)
            return sorted([curr.upper() for curr in self.ALLOWED_CURRENCIES])
        except Exception as e:
            self.logger.error(f"Error fetching currencies: {str(e)}")
            return sorted([curr.upper() for curr in self.ALLOWED_CURRENCIES])

    def get_rates(self) -> Dict:
        try:
            response = requests.get(self.ratesURL)
            if response.status_code == 200:
                data = response.json()
                filtered_rates = {
                    'date': data['date'],
                    'eur': {k: v for k, v in data['eur'].items() 
                           if k in self.ALLOWED_CURRENCIES}
                }
                return filtered_rates
            return None
        except Exception as e:
            self.logger.error(f"Error fetching rates: {str(e)}")
            return None

    def currconv(self, amount: str, source_curr: str, dest_curr: str) -> List:
        source_curr_lower = source_curr.lower()
        dest_curr_lower = dest_curr.lower()

        if source_curr_lower not in self.ALLOWED_CURRENCIES:
            return [f"Currency not supported: {source_curr}"]
        if dest_curr_lower not in self.ALLOWED_CURRENCIES:
            return [f"Currency not supported: {dest_curr}"]

        rates_data = self.get_rates()
        if not rates_data:
            return ["Error fetching rates"]

        try:
            date = rates_data['date']
            rates = rates_data['eur']
            
            if decimal.Decimal(amount) == 0:
                return ["Warning - amount entered must be greater than zero"]

            if source_curr_lower == 'eur':
                rate = rates[dest_curr_lower]
                converted = decimal.Decimal(amount) * decimal.Decimal(str(rate))
            elif dest_curr_lower == 'eur':
                rate = rates[source_curr_lower]
                converted = decimal.Decimal(amount) / decimal.Decimal(str(rate))
            else:
                source_rate = rates[source_curr_lower]
                dest_rate = rates[dest_curr_lower]
                eur_amount = decimal.Decimal(amount) / decimal.Decimal(str(source_rate))
                converted = eur_amount * decimal.Decimal(str(dest_rate))

            return [date, converted]
        except KeyError:
            return ["Invalid currency code"]
        except Exception as e:
            return [f"Conversion error: {str(e)}"]

    def format_number(self, number: decimal.Decimal) -> str:
        return locale.format_string("%.2f", number, grouping=True)

    def query(self, query: str) -> None:
        if not query:
            self.add_item(
                title="Currency Converter",
                subtitle="Usage: <amount> <source currency> <target currency>",
                icon=self.icon
            )
            return

        parts = query.strip().split()
        
        if len(parts) == 1:
            search_term = parts[0].upper()
            matching_currencies = [curr for curr in self.CURRENCIES if curr.startswith(search_term)]
            
            for curr in matching_currencies[:8]:
                self.add_item(
                    title=f"Currency: {curr}",
                    subtitle=f"Available currency: {curr}",
                    icon=self.icon
                )
            return

        elif len(parts) == 2:
            amount = parts[0]
            source_curr = parts[1].upper()
            
            try:
                decimal.Decimal(amount)
                
                for curr in self.CURRENCIES[:8]:
                    if curr != source_curr:
                        self.add_item(
                            title=f"Convert {amount} {source_curr} to {curr}",
                            subtitle=f"Press enter to convert to {curr}",
                            icon=self.icon
                        )
            except:
                self.add_item(
                    title="Invalid amount",
                    subtitle="Please enter a valid number",
                    icon=self.icon
                )
            return

        elif len(parts) == 3:
            amount = parts[0]
            source_curr = parts[1].upper()
            dest_curr = parts[2].upper()

            try:
                decimal.Decimal(amount)
                result = self.currconv(amount, source_curr, dest_curr)
                
                if len(result) == 2:
                    date, converted_amount = result
                    formatted_amount = self.format_number(converted_amount)
                    rate = converted_amount / decimal.Decimal(amount)
                    formatted_rate = self.format_number(rate)
                    
                    self.add_item(
                        title=f"{amount} {source_curr} = {formatted_amount} {dest_curr}",
                        subtitle=f"Rate: 1 {source_curr} = {formatted_rate} {dest_curr} (as of {date})",
                        icon=self.icon,
                        context=[amount, formatted_amount, source_curr, dest_curr],
                        copy=f"{formatted_amount} {dest_curr}"
                    )
                else:
                    self.add_item(
                        title=result[0],
                        subtitle="Please try again",
                        icon=self.icon
                    )
            except decimal.InvalidOperation:
                self.add_item(
                    title="Invalid amount",
                    subtitle="Please enter a valid number",
                    icon=self.icon
                )
            except Exception as e:
                self.add_item(
                    title="Error occurred",
                    subtitle=str(e),
                    icon=self.icon
                )

    def context_menu(self, data):
        amount, converted, source, dest = data
        self.add_item(
            title=f"Copy: {amount} {source}",
            subtitle="Copy original amount",
            icon=self.icon,
            copy=f"{amount} {source}"
        )
        self.add_item(
            title=f"Copy: {converted} {dest}",
            subtitle="Copy converted amount",
            icon=self.icon,
            copy=f"{converted} {dest}"
        )

if __name__ == "__main__":
    Currency()