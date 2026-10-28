import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
We are learning how gRPC communicates between services using a shared contract (`.proto`) and compact binary data (Protocol Buffers) instead of readable JSON used by REST. 
Because both client and server understand the same contract, data can be exchanged efficiently and decoded correctly. 
We also learn how changing the contract incorrectly can cause decoding problems, and how Protobuf uses fewer bytes for small integers through varint encoding.
  
  
    TOPIC: gRPC BASICS — BINARY DATA + SHARED CONTRACT

                    STOCK SERVICE
                    Quote("INFY", 1523.40, ...)
                            |
                +-----------+-----------+
                |                       |
                v                       v
        REST with JSON           gRPC with Protobuf
                |                       |
                v                       v
        {"symbol":"INFY",        Binary data (compact)
        "price":1523.40,               |
        "volume":1250000}              |
                |                       |
                v                       v
        Field names + values     Mostly values + field tags
                |                       |
                v                       v
        More readable             More compact
                |                       |
                +-----------+-----------+
                            |
                            v
                        NETWORK
                            |
                            v
                    RECEIVER SERVICE
                            |
                +-----------+-----------+
                |                       |
                v                       v
            REST CLIENT             gRPC CLIENT
            Reads JSON              Decodes binary
                                    using .proto contract


    HOW gRPC WORKS:
    ===============

            price.proto (shared contract)
                        |
                +------+------+
                |             |
                v             v
            Generate Java   Generate Java
            SERVER code     CLIENT code
                |             |
                v             v
            gRPC Server <---> gRPC Client
                    HTTP/2
                Binary messages
                        |
                        v
            Correctly decoded data


    WHY THE CONTRACT MATTERS:
    =========================

    SERVER WRITES:              CLIENT READS:
    1. symbol                   1. symbol
    2. price                    2. price
    3. volume                   3. volume
    4. epochMillis              4. epochMillis
            |                         |
            +-----------+-------------+
                        |
                        v
                    SAME CONTRACT
                    Correct decoding

    If the receiver assumes a different field order,
    the data can be decoded incorrectly or fail.


    VARINT:
    =======
    Small integer  -> Fewer bytes
    Large integer  -> More bytes

    Example:
    1       -> 1 byte
    300     -> 2 bytes

    (Actual Protobuf also uses field tags and type-specific
    encoding; this demo uses a simplified binary format.)


    REMEMBER:
    =========
    REST + JSON = Human-readable, easy to debug.
    gRPC + Protobuf = Compact binary, generated contract, HTTP/2.

    Use gRPC for high-volume internal communication and streaming.
    Use REST for public APIs and simple integrations.

 */
public class BinaryVsJsonDemo {

    record Quote(String symbol, double price, long volume, long epochMillis) {
    }

    static String toJson(Quote q) {
        return "{\"symbol\":\"" + q.symbol() + "\",\"price\":" + q.price()
                + ",\"volume\":" + q.volume() + ",\"epochMillis\":" + q.epochMillis() + "}";
    }

    // Binary format = the "contract": symbol(UTF), price(double), volume(long), time(long) IN THIS ORDER
    static byte[] toBinary(Quote q) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        DataOutputStream out = new DataOutputStream(bytes);
        out.writeUTF(q.symbol());
        out.writeDouble(q.price());
        out.writeLong(q.volume());
        out.writeLong(q.epochMillis());
        return bytes.toByteArray();
    }

    static Quote fromBinary(byte[] data) throws IOException {
        DataInputStream in = new DataInputStream(new ByteArrayInputStream(data));
        return new Quote(in.readUTF(), in.readDouble(), in.readLong(), in.readLong());
    }

    // Protobuf's trick for integers: "varint" = small numbers take fewer bytes
    static int varintSize(long value) {
        int size = 1;
        while ((value >>>= 7) != 0) {
            size++;
        }
        return size;
    }

    public static void main(String[] args) throws Exception {
        Quote quote = new Quote("INFY", 1523.40, 1_250_000L, 1_761_200_000_000L);

        String json = toJson(quote);
        byte[] binary = toBinary(quote);
        System.out.println("1) Same data, two encodings");
        System.out.println("   JSON   (" + json.getBytes(StandardCharsets.UTF_8).length + " bytes): " + json);
        System.out.println("   Binary (" + binary.length + " bytes): not human readable, no field names inside");

        System.out.println("\n2) Both sides share the contract, so decoding is exact");
        System.out.println("   decoded: " + fromBinary(binary));

        System.out.println("\n3) Without the contract (reader assumes a different field order) you get garbage");
        try {
            DataInputStream wrong = new DataInputStream(new ByteArrayInputStream(binary));
            String symbol = wrong.readUTF();
            long volume = wrong.readLong();          // really a double was written here
            System.out.println("   symbol=" + symbol + ", volume=" + volume + "  <- nonsense, nobody warned us");
        } catch (Exception e) {
            System.out.println("   failed: " + e);
        }
        System.out.println("   This is why gRPC generates BOTH client and server code from one .proto file.");

        System.out.println("\n4) Varint: protobuf spends fewer bytes on small numbers (fixed long = 8 bytes)");
        for (long v : new long[]{1, 300, 1_250_000L, 1_761_200_000_000L}) {
            System.out.printf("   value %,16d -> %d byte(s) as varint%n", v, varintSize(v));
        }

        System.out.println("\nWhen to pick gRPC: internal service-to-service calls with high volume, streaming, or strict contracts."
                + "\nWhen to keep REST: public APIs, browsers, easy debugging with curl.");
    }
}
