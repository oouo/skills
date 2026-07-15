package example;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {
    private final OrderRepository repository;
    private final ApplicationEventPublisher events;

    public OrderService(OrderRepository repository, ApplicationEventPublisher events) {
        this.repository = repository;
        this.events = events;
    }

    @Transactional
    public Order create(Order order) {
        Order saved = repository.save(order);
        events.publishEvent(new OrderCreated(saved.id()));
        return saved;
    }
}
