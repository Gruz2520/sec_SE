# DFD: WishList Service

```mermaid
graph TD
    A[User] -->|F1: HTTPS| B[Frontend]
    B -->|F2: POST /wishlist/items| C[FastAPI\n(API Gateway)]
    C -->|F3: JWT AuthZ| D[Auth Service\n(NFR-01, NFR-08)]
    D -->|F4: Hash pwd\nArgon2id| E[(User DB)]
    C -->|F5: Insert item| F[(Wishlist DB)]
    C -->|F6: Log req + corr_id| G[Logging\n(NFR-10)]
    H[Attacker] -.->|F7: Brute Force /login| D
    I[Scanner] -.->|F8: High freq POST| C
    J[Admin] -->|F9: View logs in Loki| G

    classDef external fill:#f9f,stroke:#c33,dashArray:5 5;
    classDef server fill:#e6f3ff,stroke:#333;
    classDef data fill:#ffe6e6,stroke:#333;
    classDef threat fill:#ffcccc,stroke:#f66;

    class A,H,I,J external
    class C,D,G server
    class E,F data
    class H,I threat

    subgraph "Trust Boundary: Backend"
        C
        D
        G
        E
        F
    end

    click D "https://example.com/docs/auth" _blank
    click G "https://loki.example.com" _blank
