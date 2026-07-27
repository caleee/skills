"""区域识别：从节点名中的 emoji 国旗提取区域代码。

新增区域时需同步更新：
- REGION_FLAGS（所有已知 emoji 国旗列表）
- REGION_MAP（国旗→区域代码映射，用于策略组生成）
- NAME_FLAG_MAP（关键词→国旗映射，用于 emoji 推断）
"""

import re

# 所有已知的 emoji 国旗（2 字符配对，用于判断节点名中是否已有国旗）
# 可通过 https://en.wikipedia.org/wiki/Regional_Indicator_Symbol 查询
REGION_FLAGS = [
    '🇭🇰', '🇺🇸', '🇯🇵', '🇸🇬', '🇨🇳',  # 原有 5 区域
    '🇬🇧', '🇩🇪', '🇫🇷', '🇰🇷', '🇮🇳', '🇨🇦', '🇦🇺', '🇷🇺', '🇧🇷', '🇳🇱',
    '🇸🇪', '🇳🇴', '🇫🇮', '🇩🇰', '🇵🇱', '🇨🇿', '🇭🇺', '🇷🇴', '🇹🇷', '🇮🇱',
    '🇦🇪', '🇿🇦', '🇲🇽', '🇦🇷', '🇨🇱', '🇵🇪', '🇵🇭', '🇹🇭', '🇻🇳', '🇮🇹',
    '🇪🇸', '🇨🇭', '🇲🇴',  # 澳门
    '🇦🇹', '🇦🇴', '🇦🇿', '🇧🇩', '🇧🇪', '🇧🇬', '🇧🇭', '🇧🇴', '🇨🇴', '🇩🇿',
    '🇪🇨', '🇪🇪', '🇪🇬', '🇪🇹', '🇬🇫', '🇬🇱', '🇬🇷', '🇭🇳', '🇭🇷', '🇮🇩',
    '🇮🇪', '🇮🇶', '🇮🇸', '🇰🇪', '🇰🇬', '🇰🇭', '🇰🇵', '🇰🇿', '🇱🇦', '🇱🇹',
    '🇱🇺', '🇱🇻', '🇲🇩', '🇲🇰', '🇲🇲', '🇲🇳', '🇲🇹', '🇲🇾', '🇳🇬', '🇳🇵',
    '🇳🇿', '🇵🇰', '🇵🇹', '🇷🇸', '🇸🇦', '🇸🇮', '🇸🇰', '🇹🇯', '🇹🇿', '🇺🇦',
    '🇺🇾', '🇺🇿', '🇦🇶',  # 南极洲
]

# 预编译 emoji 国旗正则（用于 ensure_emoji_flag 快速检测）
_FLAG_RE = re.compile('|'.join(map(re.escape, REGION_FLAGS)))

# emoji 国旗到区域代码的映射（用于生成策略组）
# 7 个常用组：香港、澳门、台湾、日本、韩国、新加坡、美国
# 非这 7 个区域的节点自动归入 others 组
REGION_MAP = [
    ('🇭🇰', 'hongkong'),
    ('🇲🇴', 'macao'),
    ('🇨🇳', 'taiwan'),
    ('🇯🇵', 'japan'),
    ('🇰🇷', 'korea'),
    ('🇸🇬', 'singapore'),
    ('🇺🇸', 'america'),
]


def get_region(name: str) -> str | None:
    """从节点名提取区域代码"""
    for emoji, code in REGION_MAP:
        if emoji in name:
            return code
    return None


# 节点名关键词 → emoji 国旗（优先级从高到低，用于无 emoji 国旗时的推断）
# 关键词全小写，匹配时对节点名做一次 .lower() 即可
_NAME_FLAG_MAP = [
    (['香港', 'hk', 'hkg', 'hong kong', 'hongkong', 'hkk', 'xianggang'], '🇭🇰'),
    (['日本', 'jp', 'jpn', 'japan', 'tokyo', '东京', 'nrt', 'tyo', '日', '日区'], '🇯🇵'),
    (['美国', 'us', 'usa', 'united states', 'unitedstates', '洛杉矶', 'lax', '硅谷', '美', '美区'], '🇺🇸'),
    (['新加坡', 'sg', 'sgp', 'singapore', '狮城', '新'], '🇸🇬'),
    (['台湾', 'tw', 'twn', 'taiwan', 'taipei', '台'], '🇨🇳'),
    (['澳门', 'mo', 'macau', 'macao'], '🇲🇴'),
    (['韩国', 'kr', 'kor', 'south korea', 'korea', '首尔', 'seoul', '韩'], '🇰🇷'),
    (['英国', 'uk', 'gb', 'gbr', 'united kingdom', 'london', '英', '伦敦'], '🇬🇧'),
    (['德国', 'de', 'deu', 'germany', 'frankfurt', '德'], '🇩🇪'),
    (['法国', 'fr', 'fra', 'france', 'paris', '法'], '🇫🇷'),
    (['俄罗斯', 'ru', 'rus', 'russia', 'moscow', '莫斯科', '俄'], '🇷🇺'),
    (['印度', 'in', 'ind', 'india', 'mumbai', '印'], '🇮🇳'),
    (['加拿大', 'ca', 'can', 'canada', 'toronto', '加'], '🇨🇦'),
    (['澳大利亚', 'au', 'aus', 'australia', 'sydney', '澳', '澳洲'], '🇦🇺'),
    (['巴西', 'br', 'bra', 'brazil', '巴'], '🇧🇷'),
    (['荷兰', 'nl', 'nld', 'netherlands', '荷'], '🇳🇱'),
    (['瑞典', 'se', 'swe', 'sweden'], '🇸🇪'),
    (['挪威', 'no', 'nor', 'norway'], '🇳🇴'),
    (['芬兰', 'fi', 'fin', 'finland'], '🇫🇮'),
    (['丹麦', 'dk', 'dnk', 'denmark'], '🇩🇰'),
    (['波兰', 'pl', 'pol', 'poland'], '🇵🇱'),
    (['土耳其', 'tr', 'tur', 'turkey', '土'], '🇹🇷'),
    (['以色列', 'il', 'isr', 'israel', '以'], '🇮🇱'),
    (['阿联酋', 'ae', 'are', 'uae', 'dubai', '迪拜'], '🇦🇪'),
    (['南非', 'za', 'zaf', 'south africa'], '🇿🇦'),
    (['墨西哥', 'mx', 'mex', 'mexico', '墨'], '🇲🇽'),
    (['菲律宾', 'ph', 'phl', 'philippines', '菲'], '🇵🇭'),
    (['泰国', 'th', 'tha', 'thailand', 'bangkok', '泰'], '🇹🇭'),
    (['越南', 'vn', 'vnm', 'vietnam', '越'], '🇻🇳'),
    (['意大利', 'it', 'ita', 'italy', '意'], '🇮🇹'),
    (['西班牙', 'es', 'esp', 'spain', '西'], '🇪🇸'),
    (['瑞士', 'ch', 'che', 'switzerland'], '🇨🇭'),
    (['马来西亚', 'my', 'mys', 'malaysia'], '🇲🇾'),
    (['印度尼西亚', 'id', 'idn', 'indonesia', '印尼'], '🇮🇩'),
    (['新西兰', 'nz', 'nzl', 'new zealand'], '🇳🇿'),
    (['葡萄牙', 'pt', 'prt', 'portugal'], '🇵🇹'),
    (['希腊', 'gr', 'grc', 'greece'], '🇬🇷'),
    (['捷克', 'cz', 'cze', 'czech'], '🇨🇿'),
    (['匈牙利', 'hu', 'hun', 'hungary'], '🇭🇺'),
    (['罗马尼亚', 'ro', 'rou', 'romania'], '🇷🇴'),
    (['奥地利', 'at', 'aut', 'austria'], '🇦🇹'),
    (['比利时', 'be', 'bel', 'belgium'], '🇧🇪'),
    (['爱尔兰', 'ie', 'irl', 'ireland'], '🇮🇪'),
    (['阿根廷', 'ar', 'arg', 'argentina'], '🇦🇷'),
    (['智利', 'cl', 'chl', 'chile'], '🇨🇱'),
    (['秘鲁', 'pe', 'per', 'peru'], '🇵🇪'),
    (['埃及', 'eg', 'egy', 'egypt'], '🇪🇬'),
    (['沙特阿拉伯', 'sa', 'sau', 'saudi', '沙特'], '🇸🇦'),
    (['哈萨克', 'kz', 'kaz', 'kazakhstan'], '🇰🇿'),
    (['乌克兰', 'ua', 'ukr', 'ukraine'], '🇺🇦'),
    (['蒙古', 'mn', 'mng', 'mongolia'], '🇲🇳'),
    (['孟加拉', 'bd', 'bgd', 'bangladesh'], '🇧🇩'),
    (['巴基斯坦', 'pk', 'pak', 'pakistan'], '🇵🇰'),
    (['尼日利亚', 'ng', 'nga', 'nigeria'], '🇳🇬'),
    (['伊拉克', 'iq', 'irq', 'iraq'], '🇮🇶'),
    (['柬埔寨', 'kh', 'khm', 'cambodia'], '🇰🇭'),
    (['老挝', 'la', 'lao', 'laos'], '🇱🇦'),
    (['缅甸', 'mm', 'mmr', 'myanmar'], '🇲🇲'),
    (['冰岛', 'is', 'isl', 'iceland'], '🇮🇸'),
    (['保加利亚', 'bg', 'bgr', 'bulgaria'], '🇧🇬'),
    (['克罗地亚', 'hr', 'hrv', 'croatia'], '🇭🇷'),
    (['斯洛伐克', 'sk', 'svk', 'slovakia'], '🇸🇰'),
    (['斯洛文尼亚', 'si', 'svn', 'slovenia'], '🇸🇮'),
    (['立陶宛', 'lt', 'ltu', 'lithuania'], '🇱🇹'),
    (['拉脱维亚', 'lv', 'lva', 'latvia'], '🇱🇻'),
    (['爱沙尼亚', 'ee', 'est', 'estonia'], '🇪🇪'),
    (['塞尔维亚', 'rs', 'srb', 'serbia'], '🇷🇸'),
    (['阿尔及利亚', 'dz', 'dza', 'algeria'], '🇩🇿'),
    (['埃塞俄比亚', 'et', 'eth', 'ethiopia'], '🇪🇹'),
    (['肯尼亚', 'ke', 'ken', 'kenya'], '🇰🇪'),
    (['坦桑尼亚', 'tz', 'tza', 'tanzania'], '🇹🇿'),
    (['巴林', 'bh', 'bhr', 'bahrain'], '🇧🇭'),
    (['阿塞拜疆', 'az', 'aze', 'azerbaijan'], '🇦🇿'),
    (['吉尔吉斯', 'kg', 'kgz', 'kyrgyzstan'], '🇰🇬'),
    (['塔吉克', 'tj', 'tjk', 'tajikistan'], '🇹🇯'),
    (['乌兹别克', 'uz', 'uzb', 'uzbekistan'], '🇺🇿'),
    (['摩尔多瓦', 'md', 'mda', 'moldova'], '🇲🇩'),
    (['北马其顿', 'mk', 'mkd', 'north macedonia', 'macedonia'], '🇲🇰'),
    (['安哥拉', 'ao', 'ago', 'angola'], '🇦🇴'),
    (['玻利维亚', 'bo', 'bol', 'bolivia'], '🇧🇴'),
    (['哥伦比亚', 'co', 'col', 'colombia'], '🇨🇴'),
    (['厄瓜多尔', 'ec', 'ecu', 'ecuador'], '🇪🇨'),
    (['洪都拉斯', 'hn', 'hnd', 'honduras'], '🇭🇳'),
    (['乌拉圭', 'uy', 'ury', 'uruguay'], '🇺🇾'),
    (['法属圭亚那', 'gf', 'guf', 'french guiana', 'guyane'], '🇬🇫'),
    (['格陵兰', 'gl', 'grl', 'greenland'], '🇬🇱'),
    (['卢森堡', 'lu', 'lux', 'luxembourg'], '🇱🇺'),
    (['马耳他', 'mt', 'mlt', 'malta'], '🇲🇹'),
    (['尼泊尔', 'np', 'npl', 'nepal'], '🇳🇵'),
    (['朝鲜', 'kp', 'prk', 'north korea'], '🇰🇵'),
    (['南极洲', 'aq', 'ata', 'antarctica', '南极'], '🇦🇶'),
]


# 区域组名 → ISO 3166-1 alpha-2 代码（用于 GEOIP 规则）
REGION_TO_ISO = {
    'hongkong': 'HK',
    'macao': 'MO',
    'taiwan': 'TW',
    'japan': 'JP',
    'korea': 'KR',
    'singapore': 'SG',
    'america': 'US',
    'uk': 'GB',
    'germany': 'DE',
    'france': 'FR',
    'russia': 'RU',
    'india': 'IN',
    'canada': 'CA',
    'australia': 'AU',
    'brazil': 'BR',
    'netherlands': 'NL',
    'sweden': 'SE',
    'norway': 'NO',
    'finland': 'FI',
    'denmark': 'DK',
    'poland': 'PL',
    'turkey': 'TR',
    'israel': 'IL',
    'uae': 'AE',
    'south africa': 'ZA',
    'mexico': 'MX',
    'philippines': 'PH',
    'thailand': 'TH',
    'vietnam': 'VN',
    'italy': 'IT',
    'spain': 'ES',
    'switzerland': 'CH',
    'malaysia': 'MY',
    'indonesia': 'ID',
    'new zealand': 'NZ',
    'portugal': 'PT',
    'greece': 'GR',
    'czech': 'CZ',
    'hungary': 'HU',
    'romania': 'RO',
    'austria': 'AT',
    'belgium': 'BE',
    'ireland': 'IE',
    'argentina': 'AR',
    'chile': 'CL',
    'peru': 'PE',
    'egypt': 'EG',
    'saudi': 'SA',
    'kazakhstan': 'KZ',
    'ukraine': 'UA',
    'mongolia': 'MN',
    'bangladesh': 'BD',
    'pakistan': 'PK',
    'nigeria': 'NG',
    'iraq': 'IQ',
    'cambodia': 'KH',
    'laos': 'LA',
    'myanmar': 'MM',
    'iceland': 'IS',
    'bulgaria': 'BG',
    'croatia': 'HR',
    'slovakia': 'SK',
    'slovenia': 'SI',
    'lithuania': 'LT',
    'latvia': 'LV',
    'estonia': 'EE',
    'serbia': 'RS',
    'algeria': 'DZ',
    'ethiopia': 'ET',
    'kenya': 'KE',
    'tanzania': 'TZ',
    'bahrain': 'BH',
    'azerbaijan': 'AZ',
    'kyrgyzstan': 'KG',
    'tajikistan': 'TJ',
    'uzbekistan': 'UZ',
    'moldova': 'MD',
    'north macedonia': 'MK',
    'angola': 'AO',
    'bolivia': 'BO',
    'colombia': 'CO',
    'ecuador': 'EC',
    'honduras': 'HN',
    'uruguay': 'UY',
    'french guiana': 'GF',
    'greenland': 'GL',
    'luxembourg': 'LU',
    'malta': 'MT',
    'nepal': 'NP',
    'north korea': 'KP',
    'antarctica': 'AQ',
}

# 所有 GEOIP 支持的 ISO 代码集合
GEOIP_CODES = set(REGION_TO_ISO.values())

def ensure_emoji_flag(name: str) -> str:
    """如果节点名不含 emoji 国旗，根据关键词推测并添加前缀。

    若节点名已有 emoji 国旗则直接返回原值；否则根据 _NAME_FLAG_MAP 中的
    关键词匹配，匹配到则在该名前添加 emoji 国旗 + 空格；无法匹配则返回原值。
    """
    if _FLAG_RE.search(name):
        return name
    name_lower = name.lower()
    for keywords, flag in _NAME_FLAG_MAP:
        for kw in keywords:
            if kw in name_lower:
                return f'{flag} {name}'
    return name