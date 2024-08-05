from django_redis import get_redis_connection
from collections import namedtuple
import time



Search = namedtuple('Search', ['keyword', 'score'])

class SearchService:
    def __init__(self):
        self.redis_conn = get_redis_connection("default")

    def search_ranking_list(self):
        key = "ranking"
        typed_tuples = self.redis_conn.zrevrange(key, 0, 9, withscores=True)
        return [Search(keyword=keyword.decode('utf-8'), score=score) for keyword, score in typed_tuples]

    def update_search_ranking(self, keyword):
        try:
            current_time = time.time()
            keyword_key = f"search_word:{keyword}"

            # 검색어 점수 업데이트
            self.redis_conn.zincrby("ranking", 1, keyword)

            # 타임스탬프를 기록하여 점수 감소 작업 예약
            self.redis_conn.zadd("search_expiry", {f"{keyword}:{current_time}": current_time + 300})  # 300초 후

            # 현재 점수를 갱신
            self.redis_conn.incr(keyword_key)

        except Exception as e:
            raise RuntimeError("Redis 작업 중 예외 발생") from e

        return f"{keyword} 인기 검색어 추가 완료"

    def handle_expired_keywords(self):
        current_time = time.time()
        expired_keywords = self.redis_conn.zrangebyscore("search_expiry", 0, current_time)

        for keyword_with_time in expired_keywords:
            keyword_str, timestamp = keyword_with_time.decode('utf-8').rsplit(":", 1)
            current_score = self.redis_conn.zscore("ranking", keyword_str)

            if current_score is not None and current_score > 1:
                self.redis_conn.zincrby("ranking", -1, keyword_str)
            else:
                self.redis_conn.zrem("ranking", keyword_str)
                self.redis_conn.delete(f"search_word:{keyword_str}")

            # 타임스탬프 키 제거
            self.redis_conn.zrem("search_expiry", keyword_with_time)

            # 점수가 1보다 작아지면 키 삭제
            if current_score is not None and current_score <= 1:
                self.redis_conn.zrem("ranking", keyword_str)
                self.redis_conn.delete(f"search_word:{keyword_str}")


