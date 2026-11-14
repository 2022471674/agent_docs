/**
 * 个性定位欢迎信息 —— 侧边栏 announcement 卡片
 * 参考：https://xiao-ze1.github.io/posts/2370fd62.html
 * 适配：腾讯位置服务 IP 定位 API（key 由站长提供，jsonp 跨域）
 */

window.IP_CONFIG = {
  // 腾讯位置服务 WebServiceAPI key
  API_KEY: 'XWKBZ-W6V67-PRVX4-PJMDF-BXVH6-ZWFPS',
  // 博主所在地经纬度（用于计算访客距离，GCJ-02 火星坐标）
  BLOG_LOCATION: {
    lng: 113.666, // 经度
    lat: 34.666,  // 纬度
  },
  // 缓存时间（默认 1 小时，减少 API 调用）
  CACHE_DURATION: 1000 * 60 * 60,
  // 是否只在首页显示（开启后其它页面不显示此容器）
  HOME_PAGE_ONLY: true,
};

let ipLocation = null;

const insertAnnouncementComponent = () => {
  const announcementCards = document.querySelectorAll('.card-widget.card-announcement');
  if (!announcementCards.length) return;
  if (IP_CONFIG.HOME_PAGE_ONLY && !isHomePage()) {
    announcementCards.forEach(card => card.remove());
    return;
  }
  if (!document.querySelector('#welcome-info')) return;
  fetchIpInfo();
};

const getWelcomeInfoElement = () => document.querySelector('#welcome-info');

// 腾讯位置服务 IP 定位（jsonp 跨域）
const fetchIpData = () => new Promise((resolve, reject) => {
  const cbName = '__qq_ip_cb_' + Date.now();
  const script = document.createElement('script');
  const cleanup = () => {
    try { delete window[cbName]; } catch (e) { window[cbName] = undefined; }
    if (script.parentNode) script.parentNode.removeChild(script);
  };
  window[cbName] = (res) => {
    cleanup();
    if (res && res.status === 0) {
      resolve(res);
    } else {
      reject(new Error((res && res.message) || 'IP 定位失败'));
    }
  };
  script.onerror = () => {
    cleanup();
    reject(new Error('网络请求失败'));
  };
  script.src = `https://apis.map.qq.com/ws/location/v1/ip?key=${encodeURIComponent(IP_CONFIG.API_KEY)}&output=jsonp&callback=${cbName}`;
  document.head.appendChild(script);
});

const showWelcome = (res) => {
  if (!res || !res.result) return showErrorMessage();
  const { ad_info, location, ip } = res.result;

  const welcomeInfo = getWelcomeInfoElement();
  if (!welcomeInfo) return;

  let dist = null;
  let lng = null, lat = null;
  if (location && typeof location.lng === 'number' && typeof location.lat === 'number') {
    lng = location.lng;
    lat = location.lat;
    dist = calculateDistance(lng, lat);
  }

  const pos = formatLocation(ad_info);
  const ipDisplay = formatIpDisplay(ip);

  welcomeInfo.style.display = 'block';
  welcomeInfo.style.height = 'auto';
  welcomeInfo.innerHTML = generateWelcomeMessage(pos, dist, ipDisplay, ad_info);
};

const calculateDistance = (lng, lat) => {
  const R = 6371; // 地球半径(km)
  const rad = Math.PI / 180;
  const dLat = (lat - IP_CONFIG.BLOG_LOCATION.lat) * rad;
  const dLon = (lng - IP_CONFIG.BLOG_LOCATION.lng) * rad;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(IP_CONFIG.BLOG_LOCATION.lat * rad) * Math.cos(lat * rad) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
};

const formatIpDisplay = (ip) => {
  ip = String(ip || '');
  return ip.includes(':') ? '<br>好复杂，咱看不懂~(ipv6)' : ip;
};

const formatLocation = (ad_info) => {
  if (!ad_info) return '神秘地区';
  const nation = ad_info.nation || '';
  const province = ad_info.province || '';
  const city = ad_info.city || '';
  const district = ad_info.district || '';
  if (nation && nation !== '中国') return nation;
  if (!province) return '神秘地区';
  const p = province.replace(/[省市自治区特别行政区]+$/, '');
  const c = city ? city.replace(/市$/, '') : '';
  if (!c || c === p) return p;
  return `${p} ${c}`;
};

const generateWelcomeMessage = (pos, dist, ipDisplay, ad_info) => {
  const distText = (dist !== null) ? `${dist}` : '??';
  return `欢迎来自 <b><span style="color: var(--kouseki-ip-color); font-size: var(--kouseki-gl-size)">${pos}</span></b> 的小友~<br>
    ${getGreeting(ad_info)}<br>
    当前位置距博主约 <b><span style="color: var(--kouseki-ip-color)">${distText}</span></b> 公里！<br>
    您的IP地址为：<b class="ip-address">${ipDisplay}</b><br>
    ${getTimeGreeting()}<br>`;
};

const addStyles = () => {
  const style = document.createElement('style');
  style.textContent = `
    #welcome-info {
      user-select: none;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 180px;
      padding: 10px;
      margin-top: 5px;
      border-radius: 12px;
      background-color: var(--anzhiyu-background);
      outline: 1px solid var(--anzhiyu-card-border);
      line-height: 1.8;
    }
    .loading-spinner {
      width: 50px; height: 50px;
      border: 3px solid rgba(0,0,0,0.1);
      border-radius: 50%;
      border-top: 3px solid var(--anzhiyu-main);
      animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .ip-address { filter: blur(5px); transition: filter 0.3s ease; }
    .ip-address:hover { filter: blur(0); }
    .error-message { color: #ff6565; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .error-message p { margin: 0; }
    .error-icon { font-size: 3rem; }
    #retry-button { margin: 0 5px; color: var(--anzhiyu-main); cursor: pointer; transition: transform 0.3s ease; }
    #retry-button:hover { transform: rotate(180deg); }
  `;
  document.head.appendChild(style);
};

const IP_CACHE_KEY = 'ip_info_cache';
const getIpInfoFromCache = () => {
  const cached = localStorage.getItem(IP_CACHE_KEY);
  if (!cached) return null;
  try {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp > IP_CONFIG.CACHE_DURATION) {
      localStorage.removeItem(IP_CACHE_KEY);
      return null;
    }
    return data;
  } catch (e) { return null; }
};
const setIpInfoCache = (data) => {
  localStorage.setItem(IP_CACHE_KEY, JSON.stringify({ data, timestamp: Date.now() }));
};

const fetchIpInfo = async () => {
  showLoadingSpinner();
  const cachedData = getIpInfoFromCache();
  if (cachedData) { showWelcome(cachedData); return; }
  try {
    const data = await fetchIpData();
    setIpInfoCache(data);
    showWelcome(data);
  } catch (error) {
    console.error('获取IP信息失败:', error);
    showErrorMessage();
  }
};

const showLoadingSpinner = () => {
  const el = document.querySelector('#welcome-info');
  if (!el) return;
  el.innerHTML = '<div class="loading-spinner"></div>';
};

const showErrorMessage = (message = '抱歉，无法获取信息') => {
  const el = document.getElementById('welcome-info');
  if (!el) return;
  el.innerHTML = `
    <div class="error-message">
      <div class="error-icon">🌐</div>
      <p>${message}</p>
      <p>请<i id="retry-button" class="fa-solid fa-arrows-rotate"></i>重试或检查网络连接</p>
    </div>`;
  document.getElementById('retry-button').addEventListener('click', fetchIpInfo);
};

const isHomePage = () =>
  window.location.pathname === '/' || window.location.pathname === '/index.html';

const greetings = {
  '北京市': '北——京——欢迎你~~~',
  '天津市': '讲段相声吧',
  '河北省': '山势巍巍成壁垒，天下雄关铁马金戈由此向，无限江山',
  '山西省': '展开坐具长三尺，已占山河五百余',
  '内蒙古自治区': '天苍苍，野茫茫，风吹草低见牛羊',
  '辽宁省': '我想吃烤鸡架！',
  '吉林省': '状元阁就是东北烧烤之王',
  '黑龙江省': '很喜欢哈尔滨大剧院',
  '上海市': '众所周知，中国只有两个城市',
  '江苏省': '散装是必须要散装的',
  '浙江省': '东风渐绿西湖柳，雁已还人未南归',
  '河南省': '可否带我品尝河南烩面啦？',
  '安徽省': '蚌埠住了，芜湖起飞',
  '福建省': '井邑白云间，岩城远带山',
  '江西省': '落霞与孤鹜齐飞，秋水共长天一色',
  '山东省': '遥望齐州九点烟，一泓海水杯中泻',
  '湖北省': '来碗热干面~',
  '湖南省': '74751，长沙斯塔克',
  '广东省': '来两斤福建人~',
  '广西壮族自治区': '桂林山水甲天下',
  '海南省': '朝观日出逐白浪，夕看云起收霞光',
  '四川省': '康康川妹子',
  '贵州省': '茅台，学生，再塞200',
  '云南省': '玉龙飞舞云缠绕，万仞冰川直耸天',
  '西藏自治区': '躺在茫茫草原上，仰望蓝天',
  '陕西省': '来份臊子面加馍',
  '甘肃省': '羌笛何须怨杨柳，春风不度玉门关',
  '青海省': '牛肉干和老酸奶都好好吃',
  '宁夏回族自治区': '大漠孤烟直，长河落日圆',
  '新疆维吾尔自治区': '驼铃古道丝绸路，胡马犹闻唐汉风',
  '台湾省': '我在这头，大陆在那头',
  '香港特别行政区': '永定贼有残留地鬼嚎，迎击光非岁玉',
  '澳门特别行政区': '性感荷官，在线发牌',
};

const getGreeting = (ad_info) => {
  if (!ad_info) return '带我去你的城市逛逛吧！';
  const province = ad_info.province || '';
  const p = province.replace(/[省市自治区特别行政区]+$/, '');
  return greetings[p] || '带我去你的城市逛逛吧！';
};

const getTimeGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 5) return '夜深了，早点休息，少熬夜';
  if (hour < 11) return '早上好🌅，一日之计在于晨';
  if (hour < 13) return '中午好☀️，记得午休喔~';
  if (hour < 17) return '下午好🍵，饮茶先啦！';
  if (hour < 19) return '即将下班🌇，记得按时吃饭~';
  return '晚上好🌙，夜生活嗨起来！';
};

document.addEventListener('DOMContentLoaded', () => {
  addStyles();
  insertAnnouncementComponent();
  document.addEventListener('pjax:complete', insertAnnouncementComponent);
});
