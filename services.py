from schemas import Item


class PredictionService:
    @staticmethod
    def predict_approval(item: Item) -> bool:
        if item.is_verified_seller:
            return True

        return item.images_qty > 0
