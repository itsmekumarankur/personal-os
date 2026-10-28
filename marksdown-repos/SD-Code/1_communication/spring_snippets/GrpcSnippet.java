package com.example.snippets;

import com.example.pricing.grpc.PriceReply;
import com.example.pricing.grpc.PriceRequest;
import com.example.pricing.grpc.PriceServiceGrpc;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

import java.util.concurrent.TimeUnit;

/**
 * 
 * This code teaches us how two applications communicate using gRPC in plain java(no Spring needed). 
  
   Server:
   =======
    -   provides stock prices, 

   The client:
   ==========
    -    requests a price for a stock like INFY.
    -    sends a request through a communication channel


   gRPC:
    -  is like a fast messenger between two applications, 
    -  using a predefined format for requests and responses.

    CLIENT                         SERVER
    |                               |
    |  1. Ask: INFY price?          |
    | ----------------------------> |
    |                               |
    |                     2. Process request
    |                     3. Find price: 1523.40
    |                               |
    |  4. Reply: Price = 1523.40    |
    | <---------------------------- |
    |                               |
    v                               v
    Use the price                 Send response


            HOW gRPC HELPS
    ---------------------------
    • Client and server agree on
        a common message format.
    • gRPC carries the request
        and response.
    • Protobuf defines the format.
    • HTTP/2 carries the messages.


    price.proto:
    ===========
     - is the rulebook that tells both client and server what request to send, 
     - what response to return, and which operations are available. 
     - Both sides use the same contract, so they understand each other.

              price.proto
    ---------------------------
       (Common Agreement)
                |
       +--------+--------+
       |                 |
       v                 v
   gRPC CLIENT       gRPC SERVER
       |                 |
       +------ Agree ----+
          on the rules


        1. REQUEST FORMAT

            PriceRequest
                +----------------+
                | symbol = "INFY"|
                +----------------+
                        |
                        v
                Server knows what to expect


        2. RESPONSE FORMAT

            PriceReply
                +--------------------+
                | symbol = "INFY"    |
                | price = 1523.40    |
                | epoch_millis = ... |
                +--------------------+

        
 * 
*/


public class GrpcSnippet {

    // ----------------------------------------------------------- SERVER
    static class PriceServiceImpl extends PriceServiceGrpc.PriceServiceImplBase {
        @Override
        public void getPrice(PriceRequest request, StreamObserver<PriceReply> responseObserver) {
            PriceReply reply = PriceReply.newBuilder()
                    .setSymbol(request.getSymbol())
                    .setPrice(1523.40)
                    .setEpochMillis(System.currentTimeMillis())
                    .build();
            responseObserver.onNext(reply);        // send the response
            responseObserver.onCompleted();        // finish the call
        }

        @Override
        public void streamPrices(PriceRequest request, StreamObserver<PriceReply> responseObserver) {
            for (int i = 0; i < 5; i++) {          // push 5 ticks, then end
                responseObserver.onNext(PriceReply.newBuilder()
                        .setSymbol(request.getSymbol())
                        .setPrice(1523.40 + i)
                        .setEpochMillis(System.currentTimeMillis())
                        .build());
            }
            responseObserver.onCompleted();
        }
    }

    // ----------------------------------------------------------- CLIENT
    static void callIt() throws Exception {
        ManagedChannel channel = ManagedChannelBuilder.forAddress("localhost", 9090)
                .usePlaintext()                    // use TLS in real life
                .build();

        // Blocking stub: looks like a local method call. Deadline = timeout (set one on EVERY call)
        PriceServiceGrpc.PriceServiceBlockingStub stub =
                PriceServiceGrpc.newBlockingStub(channel).withDeadlineAfter(1, TimeUnit.SECONDS);

        PriceReply reply = stub.getPrice(PriceRequest.newBuilder().setSymbol("INFY").build());
        System.out.println(reply.getSymbol() + " = " + reply.getPrice());

        channel.shutdown().awaitTermination(2, TimeUnit.SECONDS);

        /**
         * 
            Create gRPC Channel
            (localhost:9090)
                |
                v
                    Create Blocking Stub
                    (Client helper to call server)
                        |
                        v
                    Send request: getPrice("INFY")
                        |
                        v
                    PriceServiceImpl.getPrice()
                        |
                        v
                    Server creates PriceReply
                    Symbol = INFY
                    Price  = 1523.40
                                        |
                                        v
                                            Server sends response to Client
                                                |
                                                v
                                            Client prints: INFY = 1523.4
                                                |
                                                v
                                            Close Channel
         * 
        */
    }


    public static void main(String[] args) throws Exception {
        Server server = ServerBuilder.forPort(9090)
                .addService(new PriceServiceImpl())
                .build()
                .start();
        System.out.println("gRPC server listening on 9090");
        callIt();
        server.shutdown();

         /** main() starts
            |
            v
                Start gRPC Server on port 9090
                    |
                    v
                        Register PriceServiceImpl
                            |
                            v
                        Call callIt()
                    |
                    v
                Shut down gRPC Server
        */
    }
}

