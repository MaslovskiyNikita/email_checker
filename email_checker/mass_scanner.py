import json
import time
import requests
import re
from datetime import datetime
import random
import socket
import concurrent.futures
import os
from bs4 import BeautifulSoup
import threading
from queue import Queue
import logging
from urllib.parse import quote_plus, urlparse
import itertools

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MassWebsiteEmailScanner:
    def __init__(self, proxies=None, max_workers=20):
        self.stats = {
            'total_sites_checked': 0,
            'sites_with_emails': 0,
            'total_emails_found': 0,
            'start_time': datetime.now().isoformat(),
            'sites_processed': 0,
            'search_sites_found': 0
        }
        self.found_emails = set()
        self.visited_urls = set()
        self.proxies = proxies or []
        self.current_proxy = None
        self.session = requests.Session()
        self.max_workers = max_workers
        self.url_queue = Queue()
        self.email_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # Случайные User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
        
        # Настройка сессии
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.session.timeout = 10
        
        # Отключаем предупреждения SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def setup_proxy(self):
        """Настройка прокси для запросов"""
        if not self.proxies:
            return None
            
        proxy_str = random.choice(self.proxies)
        logger.info(f"Используется прокси: {proxy_str.split(':')[0]}...")
        
        try:
            if len(proxy_str.split(':')) == 4:
                ip, port, username, password = proxy_str.split(':')
                proxy_url = f"http://{username}:{password}@{ip}:{port}"
            else:
                # Если прокси без авторизации
                proxy_url = f"http://{proxy_str}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Тестируем прокси
            test_response = self.session.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=5,
                verify=False
            )
            
            if test_response.status_code == 200:
                self.current_proxy = proxies
                logger.info("Прокси успешно настроен")
                return proxies
            else:
                logger.error("Прокси не отвечает")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка настройки прокси: {e}")
            return None

    def search_sites_by_query(self, query, max_results=100):
        """Поиск сайтов по ключевому запросу через различные поисковые системы"""
        logger.info(f"🔍 Поиск сайтов по запросу: '{query}'")
        all_domains = set()
        
        # Методы поиска с весами (чем больше вес, тем чаще используется)
        search_methods = [
            (self.search_google, 3),
            (self.search_bing, 2),
            (self.search_yandex, 2),
            (self.search_duckduckgo, 1),
        ]
        
        # Запускаем методы поиска в случайном порядке
        methods = random.sample(search_methods, len(search_methods))
        
        for search_method, weight in methods:
            if len(all_domains) >= max_results:
                break
                
            try:
                logger.info(f"Пробуем {search_method.__name__}...")
                domains = search_method(query, max_results - len(all_domains))
                if domains:
                    all_domains.update(domains)
                    logger.info(f"✅ {search_method.__name__} нашёл {len(domains)} сайтов")
                    
                    # Небольшая задержка между запросами к разным поисковикам
                    time.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                logger.error(f"❌ Ошибка в {search_method.__name__}: {e}")
                continue
        
        # Если не нашли через поисковики, используем резервные методы
        if not all_domains:
            logger.info("Используем резервные методы поиска...")
            backup_domains = self.search_backup_methods(query, max_results)
            all_domains.update(backup_domains)
        
        # Проверяем существование найденных доменов
        valid_domains = []
        for domain in list(all_domains)[:max_results]:
            if self.check_domain_exists(domain):
                valid_domains.append(domain)
        
        logger.info(f"✅ Всего валидных сайтов после проверки: {len(valid_domains)}")
        
        with self.stats_lock:
            self.stats['search_sites_found'] = len(valid_domains)
            
        return valid_domains

    def search_google(self, query, max_results):
        """Поиск через Google"""
        domains = set()
        try:
            encoded_query = quote_plus(query)
            search_url = f"https://www.google.com/search?q={encoded_query}&num={min(max_results, 50)}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            response = self.session.get(
                search_url,
                headers=headers,
                proxies=self.current_proxy,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем обычные ссылки в результатах
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/url?q='):
                        url = href.split('/url?q=')[1].split('&')[0]
                        domain = self.extract_domain(url)
                        if domain and domain not in domains:
                            domains.add(domain)
                            if len(domains) >= max_results:
                                break
                
                # Альтернативный метод поиска ссылок
                if not domains:
                    links = re.findall(r'https?://[^\s&]+', response.text)
                    for link in links:
                        domain = self.extract_domain(link)
                        if domain and 'google' not in domain and domain not in domains:
                            domains.add(domain)
                            if len(domains) >= max_results:
                                break
                                
        except Exception as e:
            logger.debug(f"Google search error: {e}")
            
        return list(domains)

    def search_bing(self, query, max_results):
        """Поиск через Bing"""
        domains = set()
        try:
            encoded_query = quote_plus(query)
            search_url = f"https://www.bing.com/search?q={encoded_query}&count={min(max_results, 50)}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = self.session.get(
                search_url,
                headers=headers,
                proxies=self.current_proxy,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем ссылки в результатах Bing
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'bing.com' not in href:
                        domain = self.extract_domain(href)
                        if domain and domain not in domains:
                            domains.add(domain)
                            if len(domains) >= max_results:
                                break
                                
        except Exception as e:
            logger.debug(f"Bing search error: {e}")
            
        return list(domains)

    def search_yandex(self, query, max_results):
        """Поиск через Yandex"""
        domains = set()
        try:
            encoded_query = quote_plus(query)
            search_url = f"https://yandex.ru/search/?text={encoded_query}&numdoc={min(max_results, 50)}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                'Referer': 'https://yandex.ru/',
            }
            
            response = self.session.get(
                search_url,
                headers=headers,
                proxies=self.current_proxy,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                # Yandex часто использует JavaScript, но попробуем найти ссылки
                links = re.findall(r'https?://[^\s"<>]+', response.text)
                for link in links:
                    if 'yandex' not in link and 'yandex' not in link:
                        domain = self.extract_domain(link)
                        if domain and domain not in domains:
                            domains.add(domain)
                            if len(domains) >= max_results:
                                break
                                
        except Exception as e:
            logger.debug(f"Yandex search error: {e}")
            
        return list(domains)

    def search_duckduckgo(self, query, max_results):
        """Поиск через DuckDuckGo"""
        domains = set()
        try:
            encoded_query = quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            response = self.session.get(
                search_url,
                proxies=self.current_proxy,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', {'class': 'result__url'}):
                    url = link.text.strip()
                    if url:
                        domain = self.extract_domain(url)
                        if domain and domain not in domains:
                            domains.add(domain)
                            if len(domains) >= max_results:
                                break
                                
        except Exception as e:
            logger.debug(f"DuckDuckGo search error: {e}")
            
        return list(domains)

    def search_backup_methods(self, query, max_results):
        """Резервные методы поиска сайтов"""
        domains = set()
        
        # 1. Генерация доменов по ключевым словам
        keywords = query.lower().split()
        tlds = ['com', 'net', 'org', 'ru', 'ua', 'kz', 'by']
        
        for keyword in keywords:
            for tld in tlds:
                if len(domains) >= max_results:
                    break
                domains.add(f"{keyword}.{tld}")
        
        # 2. Использование публичных каталогов сайтов
        try:
            # Категории в DMOZ
            dmoz_urls = [
                f"http://www.dmoz.org/search?q={quote_plus(query)}",
            ]
            for url in dmoz_urls:
                if len(domains) >= max_results:
                    break
                try:
                    response = self.session.get(url, timeout=10, verify=False)
                    if response.status_code == 200:
                        found_domains = re.findall(r'https?://([^/]+)', response.text)
                        for domain in found_domains:
                            if domain and 'dmoz' not in domain:
                                domains.add(domain.replace('www.', ''))
                                if len(domains) >= max_results:
                                    break
                except:
                    continue
        except:
            pass
            
        return list(domains)

    def extract_domain(self, url):
        """Извлечение домена из URL"""
        try:
            # Если это уже домен, а не URL
            if not url.startswith('http'):
                url = 'http://' + url
                
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Убираем www
            if domain.startswith('www.'):
                domain = domain[4:]
                
            # Проверяем что домен валидный
            if '.' in domain and len(domain) > 3:
                return domain
        except:
            pass
        return None

    def load_domains_from_sources(self, max_domains=10000):
        """Загрузка доменов из различных источников с ограничением"""
        domains = set()
        
        # 1. Используем публичные списки доменов
        public_domain_sources = [
            "https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-top-domains.txt",
            "https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-random-domains.txt",
        ]
        
        for source in public_domain_sources:
            try:
                logger.info(f"Загрузка доменов из: {source}")
                response = self.session.get(source, timeout=10)
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    for line in lines:
                        if len(domains) >= max_domains:
                            break
                        domain = line.strip().lower()
                        if domain and '.' in domain and not domain.startswith('#'):
                            domains.add(domain)
                    logger.info(f"Загружено {len(domains)} доменов из {source}")
            except Exception as e:
                logger.error(f"Ошибка загрузки из {source}: {e}")
        
        # 2. Генерация доменов по шаблонам
        needed_domains = max_domains - len(domains)
        if needed_domains > 0:
            logger.info(f"Генерация {needed_domains} дополнительных доменов")
            generated_domains = self.generate_domains(needed_domains)
            domains.update(generated_domains)
        
        # 3. Загрузка из файла, если есть
        try:
            with open('domains.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if len(domains) >= max_domains:
                        break
                    domain = line.strip()
                    if domain:
                        domains.add(domain)
        except FileNotFoundError:
            pass
            
        logger.info(f"Итого загружено доменов: {len(domains)}")
        return list(domains)

    def generate_domains(self, count=10000):
        """Генерация доменов по шаблонам"""
        domains = set()
        
        # Базовые слова для генерации
        words = [
            'tech', 'digital', 'global', 'smart', 'quick', 'easy', 'fast', 'neo', 
            'meta', 'hyper', 'alpha', 'beta', 'gamma', 'prime', 'elite', 'pro',
            'max', 'ultra', 'mega', 'super', 'net', 'web', 'cloud', 'data',
            'info', 'sys', 'online', 'soft', 'hard', 'code', 'app', 'dev'
        ]
        
        tlds = ['com', 'net', 'org', 'info', 'biz', 'ru', 'ua', 'by', 'kz']
        
        # Генерация комбинаций
        for word1 in words:
            for word2 in words:
                if len(domains) >= count:
                    return list(domains)
                for tld in tlds:
                    if len(domains) >= count:
                        return list(domains)
                    domains.add(f"{word1}{word2}.{tld}")
        
        # Добавляем домены с числами
        for word in words:
            for i in range(100, 500):
                if len(domains) >= count:
                    return list(domains)
                for tld in ['com', 'net']:
                    if len(domains) >= count:
                        return list(domains)
                    domains.add(f"{word}{i}.{tld}")
        
        return list(domains)

    def check_domain_exists(self, domain):
        """Проверка существования домена через DNS"""
        try:
            socket.gethostbyname(domain)
            return True
        except:
            return False

    def find_existing_domains(self, domains_list, max_domains=5000):
        """Многопоточная проверка существования доменов"""
        logger.info(f"Проверка существования {len(domains_list)} доменов...")
        existing_domains = []
        
        # Используем ThreadPoolExecutor для DNS проверок
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(50, self.max_workers)) as executor:
            future_to_domain = {
                executor.submit(self.check_domain_exists, domain): domain 
                for domain in domains_list[:max_domains * 3]
            }
            
            for future in concurrent.futures.as_completed(future_to_domain):
                if len(existing_domains) >= max_domains:
                    break
                    
                domain = future_to_domain[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        existing_domains.append(domain)
                        if len(existing_domains) % 100 == 0:
                            logger.info(f"Найдено существующих доменов: {len(existing_domains)}")
                except Exception as e:
                    continue
        
        logger.info(f"Найдено существующих доменов: {len(existing_domains)}")
        return existing_domains

    def extract_emails_from_text(self, text):
        """Извлечение email адресов из текста"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))

    def scan_single_url(self, url):
        """Сканирование одного URL на наличие email"""
        if self.stop_event.is_set():
            return
            
        try:
            # Случайный User-Agent для каждого запроса
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # Пробуем оба протокола если не указан
            if not url.startswith('http'):
                test_urls = [f'https://{url}', f'http://{url}']
                original_url = url
            else:
                test_urls = [url]
                original_url = url
            
            response = None
            final_url = None
            
            for test_url in test_urls:
                try:
                    logger.debug(f"Попытка подключения к: {test_url}")
                    response = self.session.get(
                        test_url,
                        proxies=self.current_proxy,
                        timeout=8,
                        allow_redirects=True,
                        verify=False,
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        final_url = test_url
                        # Ограничиваем размер контента
                        response.raw.decode_content = True
                        content = response.content[:500000]
                        response._content = content
                        break
                    else:
                        logger.debug(f"Статус {response.status_code} для {test_url}")
                        response = None
                except Exception as e:
                    logger.debug(f"Ошибка подключения к {test_url}: {e}")
                    continue
            
            if not response or response.status_code != 200:
                with self.stats_lock:
                    self.stats['total_sites_checked'] += 1
                    self.stats['sites_processed'] += 1
                return None
            
            # Определяем кодировку
            if response.encoding is None:
                response.encoding = 'utf-8'
            
            try:
                text = response.text
            except UnicodeDecodeError:
                for encoding in ['windows-1251', 'cp1251', 'iso-8859-1']:
                    try:
                        text = response.content.decode(encoding)
                        break
                    except:
                        continue
                else:
                    text = response.content.decode('utf-8', errors='ignore')
            
            emails = self.extract_emails_from_text(text)
            
            # Также ищем в ссылках mailto:
            mailto_emails = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', text)
            emails.extend(mailto_emails)
            
            # Обновляем статистику
            with self.stats_lock:
                self.stats['total_sites_checked'] += 1
                self.stats['sites_processed'] += 1
                
                if emails:
                    self.stats['sites_with_emails'] += 1
                    self.stats['total_emails_found'] += len(emails)
                    with self.email_lock:
                        self.found_emails.update(emails)
                    
                    logger.info(f"🎯 Найдено {len(emails)} email на {original_url}")
                    for email in emails:
                        logger.info(f"  📧 {email}")
                    
                    # Сохраняем каждый найденный email сразу
                    self.save_emails_to_file()
                    
                    return {
                        'url': final_url or original_url,
                        'emails': emails,
                        'status': 'success'
                    }
                else:
                    if self.stats['sites_processed'] % 20 == 0:
                        logger.info(f"📊 Обработано сайтов: {self.stats['sites_processed']}, найдено email: {len(self.found_emails)}")
                    return {
                        'url': final_url or original_url,
                        'emails': [],
                        'status': 'no_emails'
                    }
                        
        except Exception as e:
            with self.stats_lock:
                self.stats['total_sites_checked'] += 1
                self.stats['sites_processed'] += 1
            logger.debug(f"Ошибка при сканировании {url}: {e}")
            return {
                'url': url,
                'emails': [],
                'status': f'error: {str(e)}'
            }

    def save_emails_to_file(self):
        """Сохранение email в файл"""
        try:
            with open('found_emails.txt', 'w', encoding='utf-8') as f:
                for email in sorted(self.found_emails):
                    f.write(f"{email}\n")
        except Exception as e:
            logger.error(f"Ошибка сохранения email: {e}")

    def save_progress(self):
        """Сохранение полного прогресса в JSON"""
        try:
            data = {
                'statistics': self.stats,
                'emails_found': list(self.found_emails),
                'last_update': datetime.now().isoformat()
            }
            with open('scan_progress.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении прогресса: {e}")

    def worker(self):
        """Рабочий поток для обработки URL"""
        while not self.stop_event.is_set():
            try:
                url = self.url_queue.get(timeout=1)
                if url is None:
                    break
                
                self.scan_single_url(url)
                self.url_queue.task_done()
                
            except:
                continue

    def run_mass_scan(self, total_sites=1000, search_query=None):
        """Запуск массового сканирования с возможностью поиска по запросу"""
        logger.info(f"🎯 Запуск массового сканирования на {total_sites} сайтов...")
        
        if search_query:
            logger.info(f"🔍 Поиск сайтов по запросу: '{search_query}'")
        
        # Настраиваем прокси
        if not self.setup_proxy():
            logger.info("⚠️ Работа без прокси")
        
        all_domains = []
        
        # Если есть поисковый запрос, сначала ищем сайты по нему
        if search_query:
            search_domains = self.search_sites_by_query(search_query, max_results=min(200, total_sites))
            all_domains.extend(search_domains)
            logger.info(f"✅ Добавлено {len(search_domains)} сайтов из поиска")
            
            # Если нашли достаточно сайтов по запросу, используем только их
            if len(search_domains) >= total_sites:
                existing_domains = search_domains[:total_sites]
            else:
                # Дополняем сайтами из других источников
                remaining_sites = total_sites - len(search_domains)
                other_domains = self.load_domains_from_sources(max_domains=remaining_sites * 2)
                existing_other_domains = self.find_existing_domains(other_domains, max_domains=remaining_sites)
                all_domains.extend(existing_other_domains)
                existing_domains = all_domains
        else:
            # Старый режим - только случайные сайты
            all_domains = self.load_domains_from_sources(max_domains=total_sites * 2)
            existing_domains = self.find_existing_domains(all_domains, max_domains=total_sites)
        
        if not existing_domains:
            logger.error("❌ Не удалось найти существующие домены")
            return
        
        logger.info(f"🚀 Начинаем сканирование {len(existing_domains)} сайтов...")
        if search_query:
            logger.info(f"📋 Из них по запросу '{search_query}': {self.stats['search_sites_found']}")
        
        # Заполняем очередь URL
        for domain in existing_domains:
            self.url_queue.put(domain)
        
        # Запускаем рабочие потоки
        threads = []
        worker_count = min(self.max_workers, len(existing_domains))
        
        for i in range(worker_count):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Мониторим прогресс
        try:
            last_count = 0
            while not self.url_queue.empty():
                current_processed = self.stats['sites_processed']
                
                if current_processed >= last_count + 10:
                    logger.info(f"📈 Прогресс: {current_processed}/{len(existing_domains)} сайтов, email: {len(self.found_emails)}")
                    last_count = current_processed
                    self.save_progress()
                
                time.sleep(1)
                
                if current_processed >= len(existing_domains):
                    break
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Сканирование прервано пользователем")
            self.stop_event.set()
        finally:
            self.url_queue.join()
            self.stop_event.set()
            time.sleep(2)
        
        self.print_final_stats()

    def print_final_stats(self):
        """Вывод финальной статистики"""
        logger.info("\n" + "="*60)
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        logger.info("="*60)
        logger.info(f"Всего проверено сайтов: {self.stats['total_sites_checked']}")
        if self.stats['search_sites_found'] > 0:
            logger.info(f"Сайтов из поиска: {self.stats['search_sites_found']}")
        logger.info(f"Сайтов с email: {self.stats['sites_with_emails']}")
        logger.info(f"Всего найдено email: {self.stats['total_emails_found']}")
        logger.info(f"Уникальных email: {len(self.found_emails)}")
        
        start_time = datetime.fromisoformat(self.stats['start_time'])
        work_time = datetime.now() - start_time
        logger.info(f"Время работы: {work_time}")

if __name__ == "__main__":
    # Прокси список
    proxy_list = [
        "191.102.154.117:9571:D2mBXc:SLokbJ",
        "191.102.172.175:9998:D2mBXc:SLokbJ",
    ]
    
    print("🎯 МАССОВЫЙ СКАНЕР EMAIL С ПОИСКОМ ПО ЗАПРОСУ")
    print("="*50)
    
    try:
        search_query = input("Введите поисковый запрос (например 'купить квартиру') или нажмите Enter для пропуска: ").strip()
        
        if search_query:
            total_sites = int(input(f"Введите количество сайтов для проверки (по умолчанию 500): ") or "500")
        else:
            total_sites = int(input("Введите количество сайтов для проверки: ") or "1000")
            
        max_workers = int(input("Введите количество потоков (20): ") or "20")
        
        print("\nВыберите режим работы:")
        print("1 - С прокси")
        print("2 - Без прокси")
        
        choice = input("Введите номер (1 или 2): ").strip()
        
        if choice == "1":
            scanner = MassWebsiteEmailScanner(proxies=proxy_list, max_workers=max_workers)
        else:
            scanner = MassWebsiteEmailScanner(proxies=[], max_workers=max_workers)
        
        # Запускаем сканирование
        scanner.run_mass_scan(total_sites=total_sites, search_query=search_query if search_query else None)
        
    except KeyboardInterrupt:
        print("\n⏹️ Сканирование прервано пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")