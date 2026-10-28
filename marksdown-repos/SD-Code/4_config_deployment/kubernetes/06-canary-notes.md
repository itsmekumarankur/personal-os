# Canary and blue-green on Kubernetes (concept, no runnable YAML here)

Blue-green: run payment-service-blue and payment-service-green Deployments (label version: v1 / v2).
Test green via its own Service, then edit the production Service selector to version: v2. Rollback = edit it back.

Canary, simple: two Deployments with the same app label, 9 replicas of v1 and 1 of v2
=> roughly 10% of traffic hits v2 (traffic split follows replica ratio).
Canary, precise and automated: Argo Rollouts, Flagger, or service-mesh weights (Istio VirtualService weight: 90/10)
with automatic analysis of error rate and automatic rollback (compare BlueGreenCanaryDemo.java).
