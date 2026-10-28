import com.github.benmanes.caffeine.cache.Caffeine;
import java.time.Duration;
import java.util.List;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Service;

/**
 * 5. Spring Cache abstraction. NOT compiled or run by the author.
 * Dependencies: spring-boot-starter-cache and either com.github.ben-manes.caffeine:caffeine (in-process)
 *               or spring-boot-starter-data-redis (shared across instances).
 */
@Configuration
@EnableCaching
class CacheConfig {
    @Bean
    CacheManager cacheManager() {
        CaffeineCacheManager manager = new CaffeineCacheManager("prices", "symbols");
        manager.setCaffeine(Caffeine.newBuilder()
                .maximumSize(10_000)                                   // ALWAYS bound the size
                .expireAfterWrite(Duration.ofMinutes(5)));             // ALWAYS set a TTL
        return manager;
    }
    // Redis: RedisCacheManager.builder(factory).cacheDefaults(RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofMinutes(5)))
}

@Service
class PriceService {

    @Cacheable(cacheNames = "prices", key = "#symbol", sync = true)    // sync=true: one loader, others wait (prevents stampede)
    public double getPrice(String symbol) { return slowLookup(symbol); }

    @Cacheable(cacheNames = "prices", key = "#symbol + ':' + #currency", unless = "#result == null")   // composite key; do not cache nulls
    public Double getPriceIn(String symbol, String currency) { return null; }

    @CacheEvict(cacheNames = "prices", key = "#symbol")                // keep cache consistent after a write
    public void updatePrice(String symbol, double price) { }

    @CacheEvict(cacheNames = "prices", allEntries = true)
    public void clearAll() { }

    @Cacheable("symbols")
    public List<String> topSymbols() { return List.of("INFY", "TCS"); }   // immutable list: safe to share

    private double slowLookup(String s) { return 1500.0; }
}

/*
 * Pitfalls recap:
 *  - Self-invocation: this.getPrice() inside the same bean bypasses the proxy, so no caching.
 *  - Per-user data: include the user/tenant in the key or do not cache.
 *  - In-process caches (Caffeine) are per instance: after an update instance 2 still serves old data until TTL.
 *    Use Redis or short TTLs, or publish an eviction event to all instances.
 *  - Cached objects are shared: never mutate them. Prefer records and immutable collections.
 *  - Cache what is expensive AND read often AND tolerant to slight staleness (reference data, prices with a TTL). Not balances.
 */
