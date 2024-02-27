from typing import List

from insurance.gateway.schemas.offer.offer import (
    OfferDriver,
    OfferVehicle,
)

from insurance.domains.policy.dto import ProductTypeEnum, Structure


class OfferStructureConverter:
    @classmethod
    def get_structure(cls, product_type: ProductTypeEnum, structures: List[Structure]) -> dict:
        handler = cls.structure_handlers[product_type]
        structure = handler(structures)
        return structure

    @staticmethod
    def _get_ogpo_vts_structure(structures: List[Structure]) -> dict:
        ogpo_vts_structure = {
            'insured': [],
            'vehicles': [],
        }
        for structure in structures:
            if structure.type == 'driver':
                ogpo_vts_structure['insured'].append(
                    OfferDriver(
                        iin=structure.attrs.iin
                    )
                )
            elif structure.type == 'vehicle':
                ogpo_vts_structure['vehicles'].append(
                    OfferVehicle(
                        registration_number=structure.attrs.registration_number
                    )
                )

        return ogpo_vts_structure

    @staticmethod
    def _get_casco_limit_structure(structures: List[Structure]) -> dict:
        casco_limit_structure = {
            'insured': [],
            'vehicle': None,
            'limit': 0,
        }
        for structure in structures:
            if structure.type == 'driver':
                casco_limit_structure['insured'].append(
                    OfferDriver(
                        iin=structure.attrs.iin
                    )
                )
            elif structure.type == 'vehicle':
                casco_limit_structure['vehicle'] = OfferVehicle(
                    registration_number=structure.attrs.registration_number
                )
            elif structure.type == 'limit':
                casco_limit_structure['limit'] = structure.attrs.value

        return casco_limit_structure

    structure_handlers = {
        ProductTypeEnum.OSGPO_VTS: _get_ogpo_vts_structure,
        ProductTypeEnum.CASCO_LIMIT: _get_casco_limit_structure,
    }
