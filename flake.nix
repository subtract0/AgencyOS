{
  description = "AgencyOS local dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python312Full
            python312Packages.pip
            python312Packages.virtualenv
            nodejs_20
            git
            openssl
            pkg-config
            docker-compose
            ollama
          ];

          shellHook = ''
            export DATABASE_URL=postgresql://agencyos:agencyos@localhost:5432/agencyos
            export VECODER_BASE_URL=http://127.0.0.1:11434
            echo "AgencyOS nix shell ready (Python $(python --version))"
          '';
        };
      }
    );
}
