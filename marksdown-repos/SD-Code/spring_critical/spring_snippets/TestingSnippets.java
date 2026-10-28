import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Bonus: Spring test slices (load only what you need, so tests start in seconds not minutes).
 * NOT compiled or run by the author. Dependency: spring-boot-starter-test (+ Testcontainers for real databases).
 *
 *   @WebMvcTest      only the web layer (controllers, advice, filters, converters). Services are mocked.
 *   @DataJpaTest     only JPA (entities, repositories) with a real or embedded DB, transaction rolled back after each test.
 *   @SpringBootTest  the whole application. Use sparingly: for a few end-to-end smoke tests.
 *   @MockitoBean     replaces a bean in the context with a Mockito mock (Spring 6.2 / Boot 3.4+; older code uses @MockBean).
 */
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean OrderLookup lookup;                                         // the controller's dependency, mocked

    @Test
    void returnsOrder() throws Exception {
        when(lookup.find(7)).thenReturn("INFY");
        mvc.perform(get("/orders/7"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.symbol").value("INFY"));
    }

    @Test
    void unknownOrderReturnsProblemDetail404() throws Exception {
        mvc.perform(get("/orders/500")).andExpect(status().isNotFound());   // exercises the @RestControllerAdvice too
    }
}

@DataJpaTest
class CustomerRepositoryTest {
    @Autowired CustomerRepository repo;

    @Test
    void listingCustomersDoesNotTriggerNPlusOne() {
        // save 20 customers with orders, then assert the number of SQL statements (e.g. with Hibernate Statistics) is <= 2
    }
}

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SmokeTest {
    @Autowired TestRestTemplate rest;

    @Test
    void healthIsUp() {
        // rest.getForEntity("/actuator/health", String.class) ...
    }
}

interface OrderLookup { String find(long id); }
interface CustomerRepository { }
class OrderController { }
