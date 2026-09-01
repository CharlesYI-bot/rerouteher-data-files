"""Reuse the verified empty-schema import generator; never run the SQL here."""
import importlib.util
from common import ROOT,STEM,PRIOR

def main():
    path=STEM/'03_REPRODUCIBILITY/build_test_import.py'
    spec=importlib.util.spec_from_file_location('masco2020_empty_schema_import',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT
    module.OLD=PRIOR
    module.PREFIX='d13_masco2020_rebuilt_20260830'
    module.TARGET_DATABASE='rerouteher_masco2020_test'
    module.build()

if __name__=='__main__':main()
