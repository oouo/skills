package example;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public record Order(@Id Long id) {
}

record OrderCreated(Long orderId) {
}
