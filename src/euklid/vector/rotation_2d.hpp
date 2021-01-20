#pragma once

#include "vector.hpp"
#include <math.h>

class Rotation2D {
    public:
        Rotation2D(double radians) {
            this->set_angle(radians);
        }
        void set_angle(double radians) {
            // np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
            this->entries[0][0] = cos(radians);
            this->entries[0][1] = sin(radians);

            this->entries[1][0] = -sin(radians);
            this->entries[1][1] = cos(radians);
        }

        Vector2D apply(const Vector2D& vector) {
            Vector2D result;

            for (int i=0; i<2; i++) {
                double coordinate = 0;
                for (int j=0; j<2; j++) {
                    coordinate += this->entries[i][j] * vector.get_item(j);
                }

                result.set_item(i, coordinate);
            }

            return result;
        }

    
    private:
        double entries[2][2];
};