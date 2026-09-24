{
  description = "hello world application using uv2nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:unrndm/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    nixpkgs,
    pyproject-nix,
    uv2nix,
    pyproject-build-systems,
    ...
  }: let
    inherit (nixpkgs) lib;
    forAllSystems = lib.genAttrs lib.systems.flakeExposed;

    workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};

    overlay = workspace.mkPyprojectOverlay {
      sourcePreference = "wheel";
    };

    editableOverlay = workspace.mkEditablePyprojectOverlay {
      root = "$REPO_ROOT";
    };

    pythonSets = forAllSystems (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (pkgs) stdenv;

        python = lib.head (pyproject-nix.lib.util.filterPythonInterpreters {
          inherit (workspace) requires-python;
          inherit (pkgs) pythonInterpreters;
        });

        pyprojectOverrides = final: prev: {
          batchedllm = prev.batchedllm.overrideAttrs (old: {
            passthru =
              old.passthru
              // {
                tests = let
                  virtualenv = final.mkVirtualEnv "batchedllm-pytest-env" {
                    batchedllm = ["all" "test"];
                  };
                in
                  (old.tests or {})
                  // {
                    pytest = stdenv.mkDerivation {
                      name = "${final.batchedllm.name}-pytest";
                      inherit (final.batchedllm) src;
                      nativeBuildInputs = [
                        virtualenv
                      ];
                      dontConfigure = true;

                      buildPhase = ''
                        runHook preBuild
                        pytest --cov batchedllm --cov-report term-missing --cov-report markdown
                        runHook postBuild
                      '';

                      outputs = [
                        "out"
                        "markdown"
                        "xml"
                      ];

                      installPhase = ''
                        runHook preInstall
                        mv ./.coverage $out
                        mv ./coverage.md $markdown
                        mv ./coverage.xml $xml
                        runHook postInstall
                      '';
                    };
                  };
              };
          });
        };
      in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
        (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.wheel
            overlay
            pyprojectOverrides
          ]
        )
    );
  in {
    devShells = forAllSystems (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonSet =
          pythonSets.${system}.overrideScope
          (
            lib.composeManyExtensions [
              editableOverlay
              (final: prev: {
                hatchling = prev.hatchling.overrideAttrs (old: {
                  passthru =
                    old.passthru
                    // {
                      dependencies =
                        old.passthru.dependencies
                        // {
                          editables = [];
                        };
                    };
                });
              })
            ]
          );
        virtualenv = pythonSet.mkVirtualEnv "batchedllm-dev-env" workspace.deps.all;
      in {
        default = pkgs.mkShell {
          packages = [
            virtualenv
            pkgs.uv
          ];
          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = pythonSet.python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };
          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)
          '';
        };
      }
    );

    packages = forAllSystems (system: {
      default =
        (pythonSets.${system}.overrideScope (final: prev: {
          outputs = ["out" "dist"];
        })).mkVirtualEnv "batchedllm-env"
        workspace.deps.default;
    });

    checks = forAllSystems (
      system: let
        pythonSet = pythonSets.${system};
      in {
        inherit (pythonSet.batchedllm.passthru.tests) pytest;
      }
    );

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);
  };
}
