import jakarta.persistence.*;
import java.util.List;
import org.hibernate.annotations.BatchSize;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 4. Fixing N+1 and lazy loading with Spring Data JPA. NOT compiled or run by the author.
 *
 * application.yml (strongly recommended):
 *   spring.jpa.open-in-view: false                         # no lazy loading in the web layer
 *   spring.jpa.properties.hibernate.default_batch_fetch_size: 50   # global safety net against N+1
 *   logging.level.org.hibernate.SQL: DEBUG                 # see what is really executed (dev only)
 *   spring.jpa.properties.hibernate.generate_statistics: true      # query counts per session
 */
@Entity
class Customer {
    @Id @GeneratedValue Long id;
    String name;

    @OneToMany(mappedBy = "customer", fetch = FetchType.LAZY)          // keep collections LAZY (the default for @OneToMany)
    @BatchSize(size = 50)                                              // fix 2: load orders for 50 customers per query
    List<Orders> orders;
}

@Entity
class Orders {
    @Id @GeneratedValue Long id;
    long amount;
    @ManyToOne(fetch = FetchType.LAZY) Customer customer;              // @ManyToOne is EAGER by default: set LAZY explicitly
}

record CustomerSummary(String name, long orderCount) { }

interface CustomerRepository extends JpaRepository<Customer, Long> {

    // fix 1a: one query with a join
    @Query("select distinct c from Customer c left join fetch c.orders")
    List<Customer> findAllWithOrders();

    // fix 1b: same without writing JPQL
    @EntityGraph(attributePaths = "orders")
    List<Customer> findByNameStartingWith(String prefix);

    // fix 3: best for read-only screens, skip entities entirely and fetch just what you display
    @Query("select new CustomerSummary(c.name, count(o)) from Customer c left join c.orders o group by c.name")
    List<CustomerSummary> summaries();
}

@Service
class CustomerService {
    private final CustomerRepository repo;
    CustomerService(CustomerRepository repo) { this.repo = repo; }

    @Transactional(readOnly = true)
    public List<CustomerSummary> list() {                              // map to DTOs INSIDE the transaction
        return repo.findAllWithOrders().stream()
                .map(c -> new CustomerSummary(c.name, c.orders.size()))
                .toList();
    }

    @Transactional
    public void rename(Long id, String newName) {
        Customer c = repo.findById(id).orElseThrow();
        c.name = newName;                                              // no save() needed: dirty checking flushes an UPDATE at commit
    }
}

/*
 * Other classic JPA traps:
 *  - Join-fetching a collection together with Pageable makes Hibernate page IN MEMORY (warning HHH000104). Fetch ids first, then details.
 *  - Never expose entities in REST responses (lazy proxies, cycles in JSON, leaking columns). Use DTOs.
 *  - Never use equals/hashCode on a generated id before it is assigned; and avoid Lombok @Data on entities.
 *  - @Transactional(readOnly = true) on query services skips dirty checking and is cheaper.
 *  - Test query counts: assert that listing 100 customers runs <= 2 SQL statements.
 */
