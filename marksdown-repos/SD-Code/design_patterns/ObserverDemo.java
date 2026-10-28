import java.util.ArrayList;
import java.util.List;

/**
 * OBSERVER - when one object changes, everyone who subscribed is told automatically.
 *
 * Real-life: a YouTube channel. You subscribe once; every time a video is uploaded
 * you get a notification. The channel does not know or care who you are, it just
 * notifies its subscribers. You can unsubscribe any time.
 *
 * Here: a stock price feed (subject) and several listeners (observers).
 * Spring's @EventListener, Kafka consumers and UI button listeners are the same idea.
 *
 * Run: java ObserverDemo.java
 */
public class ObserverDemo {

    // ---- Observer: anyone who wants to be told about price changes ----
    @FunctionalInterface
    interface PriceObserver {
        void onPriceChange(String symbol, double oldPrice, double newPrice);
    }

    // ---- Subject: keeps the subscriber list and notifies them ----
    static class StockTicker {
        private final String symbol;
        private double price;
        private final List<PriceObserver> observers = new ArrayList<>();

        StockTicker(String symbol, double initialPrice) {
            this.symbol = symbol;
            this.price = initialPrice;
        }

        void subscribe(PriceObserver observer) {
            observers.add(observer);
        }

        void unsubscribe(PriceObserver observer) {
            observers.remove(observer);
        }

        void setPrice(double newPrice) {
            double old = this.price;
            this.price = newPrice;
            // copy so an observer can unsubscribe itself while being notified
            for (PriceObserver o : new ArrayList<>(observers)) {
                o.onPriceChange(symbol, old, newPrice);
            }
        }
    }

    // ---- Concrete observers ----
    static class PortfolioTracker implements PriceObserver {
        private final int shares;

        PortfolioTracker(int shares) {
            this.shares = shares;
        }

        public void onPriceChange(String symbol, double oldPrice, double newPrice) {
            double change = (newPrice - oldPrice) * shares;
            System.out.printf("  [Portfolio] %s: your %d shares changed by %+.2f%n", symbol, shares, change);
        }
    }

    static class AlertService implements PriceObserver {
        private final double threshold;

        AlertService(double threshold) {
            this.threshold = threshold;
        }

        public void onPriceChange(String symbol, double oldPrice, double newPrice) {
            if (newPrice >= threshold) {
                System.out.printf("  [Alert] %s crossed %.2f (now %.2f)%n", symbol, threshold, newPrice);
            }
        }
    }

    public static void main(String[] args) {
        StockTicker infy = new StockTicker("INFY", 1500.00);

        PortfolioTracker portfolio = new PortfolioTracker(10);
        AlertService alert = new AlertService(1600.00);
        PriceObserver logger = (sym, oldP, newP) ->        // a lambda is a valid observer too
                System.out.println("  [Log] " + sym + " " + oldP + " -> " + newP);

        infy.subscribe(portfolio);
        infy.subscribe(alert);
        infy.subscribe(logger);

        System.out.println("Price moves to 1550:");
        infy.setPrice(1550.00);

        System.out.println("Price moves to 1620:");
        infy.setPrice(1620.00);

        System.out.println("Alert service unsubscribes, price moves to 1580:");
        infy.unsubscribe(alert);
        infy.setPrice(1580.00);
    }
}
