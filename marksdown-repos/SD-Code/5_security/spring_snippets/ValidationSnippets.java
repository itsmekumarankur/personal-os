import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.net.URI;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

/**
 * 43. Bean Validation + Spring MVC. NOT compiled or run by the author.
 * Dependency: spring-boot-starter-validation.
 */
record TransferRequest(
        @NotBlank @Pattern(regexp = "[A-Z]{2}\\d{10}", message = "must look like IN1234567890") String toAccount,
        @Min(1) @Max(10_000_000) long amountPaise,
        @NotBlank @Size(max = 140) String note) {
}

@RestController
@RequestMapping("/transfers")
class TransferController {

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    String create(@Valid @RequestBody TransferRequest request) {      // @Valid triggers validation; failure => 400 before this body runs
        return "transfer accepted";
    }
}

/** Consistent, safe 400 responses (RFC 7807 Problem Details) with field-level messages and no internals leaked. */
@RestControllerAdvice
class ValidationErrorHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail handle(MethodArgumentNotValidException ex) {
        ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        p.setType(URI.create("https://api.example.com/problems/validation"));
        List<Map<String, String>> fields = ex.getBindingResult().getFieldErrors().stream()
                .map(f -> Map.of("field", f.getField(), "message", String.valueOf(f.getDefaultMessage())))
                .toList();
        p.setProperty("errors", fields);
        return p;
    }
}

// Also: use Spring Data / JPA parameter binding (never concatenate SQL), set
// spring.servlet.multipart.max-file-size and server.tomcat.max-http-form-post-size, and validate
// @PathVariable / @RequestParam with @Validated on the controller class.
