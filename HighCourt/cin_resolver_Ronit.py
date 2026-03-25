import time

import psycopg2
import re
from itertools import product


class CINResolver:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.BankList = [
            {"CIN": "LENDER0000000000000003", "Name": "Allahabad Bank"},
            {"CIN": "LENDER0000000000000057", "Name": "Punjab National Bank"},
            {"CIN": "LENDER0000000000000069", "Name": "State Bank Of India"},
            {"CIN": "LENDER0000000000000228", "Name": "Commerce Bank"},
            {"CIN": "LENDER0000000000000033", "Name": "Indian Overseas Bank"},
            {"CIN": "LENDER0000000000000011", "Name": "Bank Of Baroda"},
            {"CIN": "LENDER000000000000624", "Name": "South Indian Bank"},
            {"CIN": "LENDER0000000000000017", "Name": "Canara Bank"},
            {"CIN": "LENDER0000000000000032", "Name": "Indian Bank"},
            {"CIN": "LENDER0000000000000099", "Name": "Uco Bank"},
            {"CIN": "LENDER0000000000000025", "Name": "Dena Bank"},
            {"CIN": "LENDER000000000000612", "Name": "Saraswat Bank"},
            {"CIN": "LENDER000000000000564", "Name": "Indusind Bank"}
        ]

    def connect_db(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.db_config['dbname'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                host=self.db_config['host'],
                port=self.db_config.get('port', 5432)
            )
            self.cursor = self.connection.cursor()
        except Exception as e:
            print(f"Database connection error: {e}")

    def close_db(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    @staticmethod
    def company_name_cutter(name):
        legal_suffixes = [
            "Limited", "limited", "LIMITED", "Limited\\.", "limited\\.", "LIMITED\\.",
            "Ltd", "ltd", "LTD", "Ltd\\.", "ltd\\.", "LTD\\.",
            "LLP", "Llp", "llp", "LLP\\.", "Llp\\.", "llp\\."
        ]
        pattern = r"^.*?\b(?:{})\b\.?".format("|".join(legal_suffixes))
        match = re.match(pattern, name)
        if match:
            return match.group(0).strip()
        return name.strip()

    @staticmethod
    def clean_company_name(name):
        if not name:
            return None

        lower_name = name.strip().lower()
        company_name = (lower_name.replace("m/s", "").replace("m/s.", "").replace("privatelimited",
                                            "private limited").replace("pvtltd", "pvt ltd").strip())

        valid_suffixes = ['ltd', 'limited', 'llp', 'bank']
        for keyword in valid_suffixes:
            if re.search(r'\b' + re.escape(keyword) + r'\b', company_name):
                return CINResolver.company_name_cutter(company_name)

        return None

    def fetch_cin(self, company_name):
        if not company_name:  # Handle None or empty case
            return None, None, None

        # Check if the exact company name exists in BankList first
        for bank in self.BankList:
            if bank["Name"].lower() == company_name.lower():
                return bank["CIN"], bank["Name"], None

        # Define abbreviation replacements for suffixes
        abbreviation_map = {
            "limited": ["Limited", "limited", "LIMITED", "Limited.", "limited.", "LIMITED.", "Ltd", "ltd", "LTD",
                          "Ltd.", "ltd.", "LTD.",],
            "ltd": ["Limited", "limited", "LIMITED", "Limited.", "limited.", "LIMITED.", "Ltd", "ltd", "LTD",
                          "Ltd.", "ltd.", "LTD."],
            "limited.": ["Limited", "limited", "LIMITED", "Limited.", "limited.", "LIMITED.", "Ltd", "ltd", "LTD",
                          "Ltd.", "ltd.", "LTD."],
            "ltd.": ["Limited", "limited", "LIMITED", "Limited.", "limited.", "LIMITED.", "Ltd", "ltd", "LTD",
                          "Ltd.", "ltd.", "LTD."],
            "private": ["Private", "private", "PRIVATE", "Pvt", "pvt", "PVT", "Pvt.", "pvt.", "PVT.", "(P)", "(p)", ""],
            "private.": ["Private", "private", "PRIVATE", "Pvt", "pvt", "PVT", "Pvt.", "pvt.", "PVT.", "(P)", "(p)", ""],
            "pvt": ["Private", "private", "PRIVATE", "Pvt", "pvt", "PVT", "Pvt.", "pvt.", "PVT.", "(P)", "(p)", ""],
            "pvt.": ["Private", "private", "PRIVATE", "Pvt", "pvt", "PVT", "Pvt.", "pvt.", "PVT.", "(P)", "(p)", ""],
            "(p)": ["Private", "private", "PRIVATE", "Pvt", "pvt", "PVT", "Pvt.", "pvt.", "PVT.", "(P)", "(p)", ""],
            "india": ["india", "India", "INDIA", "(india)", "(India)", "(INDIA)", "ind", "Ind", "IND", "(ind)", "(Ind)",
                      "(IND)", "(I)", "(i)"],
            "(india)": ["india", "India", "INDIA", "(india)", "(India)", "(INDIA)", "ind", "Ind", "IND", "(ind)",
                        "(Ind)", "(IND)", "(I)", "(i)"],
            "ind": ["india", "India", "INDIA", "(india)", "(India)", "(INDIA)", "ind", "Ind", "IND", "(ind)", "(Ind)",
                    "(IND)", "(I)", "(i)"],
            "(ind)": ["india", "India", "INDIA", "(india)", "(India)", "(INDIA)", "ind", "Ind", "IND", "(ind)", "(Ind)",
                      "(IND)", "(I)", "(i)"],
            "(i)":["india", "India", "INDIA", "(india)", "(India)", "(INDIA)", "ind", "Ind", "IND", "(ind)", "(Ind)",
                    "(IND)", "(I)", "(i)"],
            "and": ["And", "and", "AND", "&"],
            "&": ["And", "and", "AND", "&"],
            "a": ["A.", "a.", "A", "a"],
            "a.": ["A.", "a.", "A", "a"],
            "b": ["B.", "b.", "B", "b"],
            "b.": ["B.", "b.", "B", "b"],
            "c": ["C.", "c.", "C", "c"],
            "c.": ["C.", "c.", "C", "c"],
            "d": ["D.", "d.", "D", "d"],
            "d.": ["D.", "d.", "D", "d"],
            "e": ["E.", "e.", "E", "e"],
            "e.": ["E.", "e.", "E", "e"],
            "f": ["F.", "f.", "F", "f"],
            "f.": ["F.", "f.", "F", "f"],
            "g": ["G.", "g.", "G", "g"],
            "g.": ["G.", "g.", "G", "g"],
            "h": ["H.", "h.", "H", "h"],
            "h.": ["H.", "h.", "H", "h"],
            "i": ["I.", "i.", "I", "i"],
            "i.": ["I.", "i.", "I", "i"],
            "j": ["J.", "j.", "J", "j"],
            "j.": ["J.", "j.", "J", "j"],
            "k": ["K.", "k.", "K", "k"],
            "k.": ["K.", "k.", "K", "k"],
            "l": ["L.", "l.", "L", "l"],
            "l.": ["L.", "l.", "L", "l"],
            "m": ["M.", "m.", "M", "m"],
            "m.": ["M.", "m.", "M", "m"],
            "n": ["N.", "n.", "N", "n"],
            "n.": ["N.", "n.", "N", "n"],
            "o": ["O.", "o.", "O", "o"],
            "o.": ["O.", "o.", "O", "o"],
            "p": ["P.", "p.", "P", "p"],
            "p.": ["P.", "p.", "P", "p"],
            "q": ["Q.", "q.", "Q", "q"],
            "q.": ["Q.", "q.", "Q", "q"],
            "r": ["R.", "r.", "R", "r"],
            "r.": ["R.", "r.", "R", "r"],
            "s": ["S.", "s.", "S", "s"],
            "s.": ["S.", "s.", "S", "s"],
            "t": ["T.", "t.", "T", "t"],
            "t.": ["T.", "t.", "T", "t"],
            "u": ["U.", "u.", "U", "u"],
            "u.": ["U.", "u.", "U", "u"],
            "v": ["V.", "v.", "V", "v"],
            "v.": ["V.", "v.", "V", "v"],
            "w": ["W.", "w.", "W", "w"],
            "w.": ["W.", "w.", "W", "w"],
            "x": ["X.", "x.", "X", "x"],
            "x.": ["X.", "x.", "X", "x"],
            "y": ["Y.", "y.", "Y", "y"],
            "y.": ["Y.", "y.", "Y", "y"],
            "z": ["Z.", "z.", "Z", "z"],
            "z.": ["Z.", "z.", "Z", "z"],
            "co": ["CO.", "Co.", "co.", "CO", "Co", "co", "COMPANY", "Company", "company", ""],
            "co.": ["CO.", "Co.", "co.", "CO", "Co", "co", "COMPANY", "Company", "company", ""],
            "company": ["CO.", "Co.", "co.", "CO", "Co", "co", "COMPANY", "Company", "company", ""],
            "company.": ["CO.", "Co.", "co.", "CO", "Co", "co", "COMPANY", "Company", "company", ""],
            "east": ["EAST", "East", "east", "(EAST)", "(East)", "(east)", "(E)", "(e)", "E", "e"],
            "corp": ["CORP", "Corp", "corp", "CORP.", "Corp.", "corp.", "CORPORATION", "Corporation", "corporation", "CORPORATION.", "Corporation.", "corporation."],
            "corp.": ["CORP", "Corp", "corp", "CORP.", "Corp.", "corp.", "CORPORATION", "Corporation", "corporation", "CORPORATION.", "Corporation.", "corporation."],
            "corporation": ["CORP", "Corp", "corp", "CORP.", "Corp.", "corp.", "CORPORATION", "Corporation", "corporation", "CORPORATION.", "Corporation.", "corporation."]
            }

        def normalize_name(name):
            """ Removes extra spaces and converts to title case """
            return re.sub(r'\s+', ' ', name.strip()).title()

        def generate_variations(name):
            words = name.split()
            # Handle first word: support dynamic abbreviation expansion
            if '.' in words[0] and words[0].count('.') >= 1:
                first_word = words[0]
                # Split into dotted initials: "P.N." → ["P.", "N."]
                split_initials = [w + '.' for w in first_word.split('.') if w]
                # Variants:
                joined_initials = ''.join([w[0] for w in split_initials if w])  # "PN"
                spaced_initials = ' '.join([w[0] for w in split_initials if w])  # "P N"
                first_word_variants = [first_word, joined_initials, spaced_initials]
                final_words = [first_word_variants] + words[1:]
            else:
                final_words = [[words[0]]] + words[1:]
            # Apply abbreviation_map on all words
            replacement_options = []
            for word in final_words:
                if isinstance(word, list):
                    word_variants = []
                    for w in word:
                        lower_w = w.lower()
                        if lower_w in abbreviation_map:
                            word_variants.extend(abbreviation_map[lower_w])
                        else:
                            word_variants.append(w)
                    replacement_options.append(word_variants)
                else:
                    lower_word = word.lower()
                    if lower_word in abbreviation_map:
                        replacement_options.append(abbreviation_map[lower_word])
                    else:
                        replacement_options.append([word])
            # Generate all combinations
            variations = set(" ".join(words) for words in product(*replacement_options))
            variations.add(name.lower())
            variations.add(name.upper())
            variations.add(name)
            return list(variations)

        # Normalize input name
        formatted_name = normalize_name(company_name)

        # Generate variations
        name_variants = generate_variations(formatted_name)
        # print(name_variants)

        # Try searching with different variations
        count = 0
        for query_name in name_variants:
            count += 1
            print(f"{count} : Searching for: {query_name}")  # Debugging
            query_name = query_name.replace("  ", " ")
            self.cursor.execute(
                """
                SELECT cin, company_name, company_pan, status_id, created
                FROM company_core.t_company_detail
                WHERE company_name = %s
                AND status_id IN (116, 51, 52, 117, 55, 120, 118, 121, 20950)
                ORDER BY (created IS NULL), created DESC;
                """,
                (query_name,)
            )
            result = self.cursor.fetchone()
            if result:
                return result[0], result[1], result[2]

        return None, None, None


def get_cin(companyName):
    db_config = {
        'dbname': 'company_uat',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost'
    }

    cin_resolver = CINResolver(db_config)
    cin_resolver.connect_db()

    start_time = time.time()

    clean_name = cin_resolver.clean_company_name(companyName)
    print("Valid Company : ",clean_name)
    cin, name, pan = cin_resolver.fetch_cin(clean_name)
    print(name, " : ", cin, " : ", pan)
    end_time = time.time()
    cin_resolver.close_db()
    print(f"Execution Time: {end_time - start_time:.6f} seconds")
    return cin, name


if __name__ == "__main__":
    companyName = "Tata motors limited"
    print(get_cin(companyName))

