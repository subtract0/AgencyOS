{
  description = "AgencyOS - Autonomous AI Development Infrastructure";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        # Python environment with AgencyOS dependencies
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Core
          pydantic
          httpx
          requests
          openai

          # Data
          numpy
          pandas

          # Testing
          pytest
          pytest-asyncio

          # Dev tools
          ruff

          # Utilities
          python-dotenv
          rich
          typer
          fastapi
          uvicorn
        ]);

      in {
        # Development shell - `nix develop`
        devShells.default = pkgs.mkShell {
          name = "agencyos-dev";

          buildInputs = with pkgs; [
            # Python
            pythonEnv

            # Node (for Micro app)
            nodejs_22

            # Tools
            git
            gh
            jq
            curl

            # System monitoring
            htop
          ];

          shellHook = ''
            echo ""
            echo "🤖 AgencyOS Development Environment"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Python: $(python --version)"
            echo "Node:   $(node --version)"
            echo ""
            echo "Commands:"
            echo "  operator        - Start voice interface"
            echo "  daemon          - Start 24/7 autonomous daemon"
            echo "  micro-dev       - Start Micro app dev server"
            echo "  test            - Run test suite"
            echo ""

            # Aliases
            alias operator="python tools/life/voice_loop.py"
            alias daemon="python agency_daemon.py"
            alias micro-dev="cd micro && npm run dev"
            alias test="python run_tests.py"

            # Environment
            export AGENCYOS_ROOT="$(pwd)"
            export PYTHONPATH="$AGENCYOS_ROOT:$PYTHONPATH"

            # Load .env if exists
            if [ -f .env ]; then
              set -a
              source .env
              set +a
              echo "✓ Loaded .env"
            fi
          '';
        };

        # Packages
        packages = {
          # Default package
          default = pkgs.stdenv.mkDerivation {
            pname = "agencyos";
            version = "1.3.0";
            src = ./.;

            buildInputs = [ pythonEnv ];

            installPhase = ''
              mkdir -p $out/lib/agencyos
              cp -r . $out/lib/agencyos/

              mkdir -p $out/bin

              cat > $out/bin/operator <<EOF
#!/bin/sh
cd $out/lib/agencyos
exec ${pythonEnv}/bin/python tools/life/voice_loop.py "\$@"
EOF
              chmod +x $out/bin/operator

              cat > $out/bin/agency-daemon <<EOF
#!/bin/sh
cd $out/lib/agencyos
exec ${pythonEnv}/bin/python agency_daemon.py "\$@"
EOF
              chmod +x $out/bin/agency-daemon
            '';
          };

          # Docker image
          dockerImage = pkgs.dockerTools.buildImage {
            name = "agencyos";
            tag = "latest";

            copyToRoot = pkgs.buildEnv {
              name = "agencyos-root";
              paths = [
                self.packages.${system}.default
                pythonEnv
                pkgs.bashInteractive
                pkgs.coreutils
              ];
            };

            config = {
              Cmd = [ "/bin/agency-daemon" ];
              WorkingDir = "/lib/agencyos";
            };
          };
        };

        # Apps - `nix run`
        apps = {
          operator = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/operator";
          };

          daemon = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/agency-daemon";
          };

          default = self.apps.${system}.daemon;
        };
      }
    );
}
