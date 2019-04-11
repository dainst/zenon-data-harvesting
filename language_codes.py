language_codes={'af': 'afr', 'sq': 'alb', 'ar': 'ara', 'bn': 'ben', 'bg': 'bul', 'ca': 'cat', 'zh': 'chi', 'cs': 'cze', 'da': 'dan', 'nl': 'dut', 'en': 'eng', 'et': 'est', 'fi': 'fin', 'fr': 'fre', 'de': 'ger', 'el': 'gre', 'gu': 'guj', 'he': 'heb', 'hi': 'hin', 'hr': 'hrv', 'hu': 'hun', 'id': 'ind', 'it': 'ita', 'ja': 'jpn', 'kn': 'kan', 'ko': 'kor', 'lv': 'lav', 'lt': 'lit', 'mk': 'mac', 'ml': 'mal', 'mr': 'mar', 'ne': 'nep', 'no': 'nor', 'pa': 'pan', 'fa': 'per', 'pl': 'pol', 'pt': 'por', 'ro': 'rum', 'ru': 'rus', 'sk': 'slo', 'sl': 'slv', 'so': 'som', 'es': 'spa', 'sw': 'swa', 'sv': 'swe', 'ta': 'tam', 'te': 'tel', 'tl': 'tgl', 'th': 'tha', 'tr': 'tur', 'uk': 'ukr', 'ur': 'urd', 'vi': 'vie', 'cy': 'wel'}
def resolve(code):
    for tuple in language_codes.items():
        if code == tuple[0]:
            return(tuple[1])
        elif code == tuple[1]:
            return(tuple[0])